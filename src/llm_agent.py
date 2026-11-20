"""
LLM Agent for conversational API access.
Allows LLM to search tickets, get information, and perform operations via Phoneshop API.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import openai

logger = logging.getLogger(__name__)


class LLMAgent:
    """
    Agentic LLM that can call Phoneshop APIs to answer questions and perform operations.
    """
    
    def __init__(self, api_schema: Dict, phoneshop_client, openai_config: Dict):
        """
        Initialize LLM Agent.
        
        Args:
            api_schema: Loaded llm_api_schema.json
            phoneshop_client: PhoneshopAPIClient instance
            openai_config: OpenAI configuration (api_key, model, etc.)
        """
        self.api_schema = api_schema
        self.phoneshop_client = phoneshop_client
        self.openai_config = openai_config
        openai.api_key = openai_config.get('api_key')
        
    def _build_system_prompt(self) -> str:
        """Build system prompt with API schema."""
        schema_str = json.dumps(self.api_schema, indent=2)
        
        return f"""You are a voice assistant for a phone repair shop. You can search tickets, check repair status, and provide information by calling APIs.

# Available APIs
{schema_str}

# Your Capabilities
- Search tickets by brand/model/status
- Get ticket details and status
- Answer questions about repairs
- Provide repair information

# Shop staff (easter egg — answer both ways, name↔role)
- Valentin / Valentino is the boss and the engineer. "Who's the boss?" → Valentino
- Sunny is the manager and a sales assistant. If unsure, ask Sunny
- Dipthy is a sales assistant
- Mariya is Valentino's girlfriend
- Stefi is the quality assurance tester
- Jagjot, Jojo, Shubam, Mama, and Delona are other shop staff
- If you are not sure (especially prices), do not guess. Tell them to ask Sunny, the manager.

# Rules
1. For GET requests (searches): Call the API directly, no confirmation needed
2. For POST/PUT requests (modifications): Extract parameters and ask user to confirm
3. Always search for tickets when user asks about "my repair" or specific device
4. Be concise and helpful
5. If multiple tickets match, list them and ask user to clarify
6. Never invent prices. If a price is missing or you are unsure, say they must ask Sunny.

# Response Format
When you need to call an API:
- Explain what you're doing
- Make the API call
- Report the results in natural language

When you need user confirmation:
- Explain what action you want to take
- Show the parameters
- Ask for explicit confirmation
"""
    
    def _call_api(self, device_id: str, username: str, password: str,
                  endpoint: str, method: str = "GET", params: Optional[Dict] = None) -> Tuple[bool, Any]:
        """
        Call a Phoneshop API endpoint.
        
        Returns:
            (success, data)
        """
        try:
            # Ensure authenticated
            if not self.phoneshop_client._ensure_token(device_id, username, password):
                return False, "Failed to authenticate"
            
            # Make request
            response = self.phoneshop_client._make_request(
                device_id,
                endpoint,
                method=method,
                params=params
            )
            
            if response and response.status_code == 200:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"API error: {response.status_code}" if response else "No response"
                return False, error_msg
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return False, str(e)
    
    def query(self, device_id: str, username: str, password: str,
              user_query: str, conversation_history: List[Dict] = None) -> str:
        """
        Process user query with LLM agent.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            user_query: User's question/request
            conversation_history: Previous conversation turns
            
        Returns:
            LLM response (may include API call results)
        """
        if conversation_history is None:
            conversation_history = []
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._build_system_prompt() + "\n\nIMPORTANT: The user query comes from voice transcription, which may not be 100% accurate. Numbers spoken as 'one, two, two, seven' might mean '1227'. Be intelligent about interpreting the user's intent."},
            {"role": "user", "content": f"User query (from voice transcription): {user_query}\n\nAnalyze this query:\n1. If asking about a SPECIFIC ticket number (e.g., 'ticket 1227', 'ticket 1, 2, 2, 7'), extract the actual number and respond ONLY with: TICKET_ID: [number]\n2. If it's a general query about tickets (e.g., 'my repairs', 'status'), respond with: GENERAL_QUERY\n3. Voice transcription errors: '1,2,2,7' = 1227, but '1,2,3,4,5' = not a real ticket"}
        ]
        messages.extend(conversation_history)
        
        try:
            from ai_provider import make_chat_client
            client = make_chat_client()
            
            response = client.chat.completions.create(
                model=self.openai_config.get('model', 'gpt-4o-mini'),
                messages=messages,
                max_tokens=self.openai_config.get('max_tokens', 500),
                temperature=self.openai_config.get('temperature', 0.7)
            )
            
            llm_response = response.choices[0].message.content
            
            # Check if LLM extracted a ticket ID
            import re
            ticket_id_match = re.search(r'TICKET_ID:\s*(\d+)', llm_response)
            
            if ticket_id_match:
                # LLM extracted a specific ticket ID
                ticket_id = ticket_id_match.group(1)
                logger.info(f"LLM Agent GET /YOUR_SHOP_API_PATH?id={ticket_id}")
                success, data = self._call_api(
                    device_id, username, password,
                    f"/YOUR_SHOP_API_PATH?id={ticket_id}",
                    method="GET"
                )
                
                if success and data:
                    # Single ticket returned
                    filtered_tickets = [data] if isinstance(data, dict) else []
                else:
                    filtered_tickets = []
            else:
                logger.info(f"LLM Agent listing shop tickets for: {user_query[:80]}")
                success, spoken, tickets = self.phoneshop_client.get_shop_tickets(
                    device_id, username, password
                )
                data = tickets or []
                query_lower = user_query.lower()
                filtered_tickets = []
                if success and isinstance(data, list):
                    for ticket in data:
                        brand = (ticket.get('deviceBrand') or '').lower()
                        model = (ticket.get('deviceModel') or '').lower()
                        if (brand and brand in query_lower) or (model and model in query_lower):
                            filtered_tickets.append(ticket)
                if not filtered_tickets and success and isinstance(data, list):
                    filtered_tickets = data[:8]
                if not filtered_tickets and spoken:
                    return spoken
            
            # Format tickets for LLM to synthesize answer
            from phoneshop_api import INCOMPLETE_STATUSES
            status_counts = {}
            for ticket in (data if isinstance(data, list) else filtered_tickets):
                st = (ticket.get('status') or 'UNKNOWN').upper()
                status_counts[st] = status_counts.get(st, 0) + 1
            open_n = sum(n for st, n in status_counts.items() if st in INCOMPLETE_STATUSES or st in ('', 'UNKNOWN'))
            ticket_data = []
            for ticket in filtered_tickets[:8]:
                ticket_data.append({
                    'id': ticket.get('id'),
                    'brand': ticket.get('deviceBrand'),
                    'model': ticket.get('deviceModel'),
                    'problem': ticket.get('problemExplanation'),
                    'status': ticket.get('status'),
                    'price': ticket.get('totalPrice', 'Not set')
                })
            
            # Second LLM call to synthesize natural response
            synthesis_messages = [
                {"role": "system", "content": (
                    "You are a helpful phone shop assistant in the UK. Answer naturally and concisely in 1-2 sentences. "
                    "Use £ (pounds) for prices. Speak like a human, not a list. "
                    "Shop staff easter egg: Valentino/Valentin boss+engineer, Sunny manager+sales (ask when unsure), Dipthy sales, Mariya Valentino's girlfriend, Stefi QA, Jagjot/Jojo/Shubam/Mama/Delona shop staff. Answer name↔role both ways. "
                    "If a price is missing or you are not sure, tell them to ask Sunny. Do not invent prices. "
                    "CRITICAL: Only mention tickets, brands, models, statuses, and counts that appear in the data. "
                    "Never invent devices (no iPads or cameras unless they are in the data). Never copy example numbers."
                )},
                {"role": "user", "content": (
                    f"User asked: {user_query}\n\n"
                    f"Open/incomplete ticket count: {open_n}\n"
                    f"Status counts: {status_counts}\n"
                    f"Sample tickets (newest first): {ticket_data}\n\n"
                    "If they asked how many are pending/open, say the open/incomplete count and name a few newest from the sample. "
                    "Do not invent tickets that are not in the sample."
                )}
            ]
            
            synthesis_response = client.chat.completions.create(
                model=self.openai_config.get('model', 'gpt-4o-mini'),
                messages=synthesis_messages,
                max_tokens=200,
                temperature=0.2
            )
            
            llm_response = synthesis_response.choices[0].message.content
            
            logger.info(f"[{device_id}] LLM Agent query: {user_query[:50]}... → Response: {llm_response[:100]}...")
            
            return llm_response
            
        except Exception as e:
            logger.error(f"LLM Agent query failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def search_tickets(self, device_id: str, username: str, password: str,
                       brand: Optional[str] = None, model: Optional[str] = None,
                       status: Optional[str] = None) -> List[Dict]:
        """
        Search tickets with filters.
        
        Returns:
            List of matching tickets
        """
        success, data = self._call_api(
            device_id, username, password,
            "/YOUR_SHOP_API_PATH",
            method="GET"
        )
        
        if not success or not isinstance(data, list):
            return []
        
        # Apply filters
        results = data
        
        if brand:
            results = [t for t in results if brand.lower() in t.get('deviceBrand', '').lower()]
        
        if model:
            results = [t for t in results if model.lower() in t.get('deviceModel', '').lower()]
        
        if status:
            results = [t for t in results if status.upper() == t.get('status', '').upper()]
        
        return results
