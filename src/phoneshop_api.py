"""
Phoneshop API client for multi-device support.
Handles authentication, token management, and API requests.
"""
import os
import re
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, List

try:
    from zoneinfo import ZoneInfo
    LONDON_TZ = ZoneInfo("Europe/London")
except Exception:
    LONDON_TZ = timezone(timedelta(hours=1))

INCOMPLETE_STATUSES = {
    "PENDING", "STARTED", "DIAGNOSED", "WAITING_FOR_PARTS", "ON_HOLD",
    "EXPECTING_ARRIVAL", "IN_PROGRESS", "FROZEN",
}

WARRANTY_VALUES = {
    "NONE", "ONE_DAY", "THREE_DAYS", "ONE_WEEK", "TWO_WEEKS",
    "ONE_MONTH", "THREE_MONTHS", "SIX_MONTHS", "ONE_YEAR", "TWO_YEARS",
}

_WARRANTY_PATTERNS = (
    (r'\b(2|two)\s*years?\b', "TWO_YEARS"),
    (r'\b(1|one|a)\s*years?\b|\b12\s*months?\b', "ONE_YEAR"),
    (r'\b(6|six)\s*months?\b', "SIX_MONTHS"),
    (r'\b(3|three)\s*months?\b', "THREE_MONTHS"),
    (r'\b(1|one|a)\s*months?\b', "ONE_MONTH"),
    (r'\b(2|two)\s*weeks?\b', "TWO_WEEKS"),
    (r'\b(1|one|a)\s*weeks?\b', "ONE_WEEK"),
    (r'\b(3|three)\s*days?\b', "THREE_DAYS"),
    (r'\b(1|one|a)\s*days?\b', "ONE_DAY"),
    (r'\bno warranty\b|\bnone\b', "NONE"),
)


def parse_warranty(value, default: str = "ONE_MONTH") -> str:
    if value is None or value == "":
        return default
    raw = str(value).strip()
    key = raw.upper().replace(" ", "_").replace("-", "_")
    if key in WARRANTY_VALUES:
        return key
    low = raw.lower()
    for pat, enum in _WARRANTY_PATTERNS:
        if re.search(pat, low):
            return enum
    return default


def warranty_spoken(value) -> str:
    key = parse_warranty(value, default="")
    if not key:
        return ""
    return key.replace("_", " ").lower()


def london_now() -> datetime:
    return datetime.now(LONDON_TZ)

logger = logging.getLogger(__name__)

class PhoneshopAPIClient:
    """API client for Phoneshop system with per-device authentication"""
    
    BASE_URL = "https://YOUR_PHONESHOP_API_HOST"
    
    def __init__(self):
        self.device_tokens = {}  # {device_id: {'token': str, 'shop_id': int, 'expires_at': datetime}}
    
    def _ensure_token(self, device_id: str, username: str, password: str) -> bool:
        """
        Ensure we have a valid token for this device.
        Auto-refresh if expired.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            
        Returns:
            True if token is valid, False otherwise
        """
        # Check if we have a token and it's not expired
        if device_id in self.device_tokens:
            token_info = self.device_tokens[device_id]
            expires_at = token_info.get('expires_at')
            if expires_at and datetime.now(timezone.utc) < expires_at:
                return True
        
        # Need to login
        return self._login(device_id, username, password)
    
    def _login(self, device_id: str, username: str, password: str) -> bool:
        """
        Login to Phoneshop API and store token.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Use /YOUR_SHOP_API_PATH endpoint with query parameters (not /YOUR_SHOP_API_PATH with JSON)
            # Token comes back in Authorization header, not response body
            params = {"username": username, "password": password}
            response = requests.post(
                f"{self.BASE_URL}/YOUR_SHOP_API_PATH",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                # Token is in the Authorization header
                token = response.headers.get("Authorization")
                
                # User data and shop ID are in response body
                data = response.json()
                shop_id = data.get("shopId")
                
                if not token:
                    logger.error(f"Login response missing Authorization header for device {device_id}")
                    return False
                
                # Store token with 1 hour expiry (conservative)
                self.device_tokens[device_id] = {
                    'token': token,
                    'shop_id': shop_id,
                    'user_data': data,
                    'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
                }
                
                logger.info(f"Logged in device {device_id} to Phoneshop (shop_id: {shop_id})")
                return True
            else:
                logger.error(f"Login failed for device {device_id}: {response.status_code}")
                try:
                    error_body = response.text
                    logger.error(f"Response body: {error_body}")
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Login error for device {device_id}: {e}")
            return False
    
    def _make_request(self, device_id: str, endpoint: str, method: str = "GET", 
                     params: dict = None, json_data: dict = None) -> Optional[requests.Response]:
        """
        Make an authenticated API request.
        
        Args:
            device_id: Device identifier
            endpoint: API endpoint (e.g., "/YOUR_SHOP_API_PATH")
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            Response object or None if failed
        """
        token_info = self.device_tokens.get(device_id)
        if not token_info:
            logger.error(f"No token for device {device_id}")
            return None
        
        url = self.BASE_URL + endpoint
        headers = {
            "Authorization": f"Bearer {token_info['token']}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            logger.debug(f"Making {method} request to {url}")
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                # Log the exact JSON that will be sent
                import json as json_lib
                json_str = json_lib.dumps(json_data, indent=2)
                logger.info(f"📤 Exact JSON payload being sent:\n{json_str}")
                response = requests.post(url, headers=headers, json=json_data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, params=params, json=json_data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            logger.debug(f"Response status: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout as e:
            logger.error(f"API request timed out after 10s: {url} - {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API connection error: {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"API request failed: {url} - {type(e).__name__}: {e}")
            return None
    
    def _get_case_matched_model(self, device_id: str, brand: str, model: str) -> str:
        """
        Get the exact case-matched model name from the database.
        If model exists with different casing, return the database version.
        Otherwise, return the input model (will be created by backend).
        
        Args:
            device_id: Device identifier
            brand: Device brand (case-insensitive)
            model: Device model (case-insensitive)
            
        Returns:
            Case-matched model name from database, or original if not found
        """
        logger.info(f"🔍 Checking model case for: '{model}' (brand: '{brand}')")
        try:
            # Fetch all brands with their models
            logger.info(f"🌐 Fetching brands from /YOUR_SHOP_API_PATH")
            response = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="GET")
            logger.info(f"📡 Brand API response received: status={response.status_code if response else 'None'}")
            
            if not response or response.status_code != 200:
                logger.warning(f"❌ Failed to fetch brands (status={response.status_code if response else 'None'}), using model as-is: {model}")
                return model
            
            brands = response.json()
            logger.debug(f"📋 Fetched {len(brands)} brands from API")
            
            # Find matching brand (case-insensitive)
            logger.debug(f"🔎 Searching for brand '{brand}' (case-insensitive)")
            matching_brand = next(
                (b for b in brands if b.get('value', '').lower() == brand.lower()),
                None
            )
            
            if not matching_brand:
                logger.info(f"❌ Brand '{brand}' not found in database, model will be created")
                return model
            
            logger.debug(f"✅ Found brand: {matching_brand.get('value')}, checking models...")
            
            # Find matching model in brand's models (case-insensitive)
            models = matching_brand.get('models', [])
            logger.debug(f"📱 Brand has {len(models)} models")
            
            matching_model = next(
                (m for m in models if m.get('value', '').lower() == model.lower()),
                None
            )
            
            if matching_model:
                exact_model = matching_model['value']
                if exact_model != model:
                    logger.info(f"✅ Model case-matched: '{model}' → '{exact_model}'")
                else:
                    logger.info(f"✅ Model case already correct: '{model}'")
                return exact_model
            else:
                logger.info(f"❌ Model '{model}' not found for brand '{brand}', will be created")
                return model
                
        except Exception as e:
            logger.error(f"💥 Error matching model case: {type(e).__name__}: {e}", exc_info=True)
            return model
    
    def create_ticket(self, device_id: str, username: str, password: str,
                     brand: str, model: str, problem: str,
                     device_condition: Optional[str] = None,
                     accessories: Optional[str] = None,
                     total_price: Optional[float] = None,
                     deposit: Optional[float] = None,
                     device_password: Optional[str] = None,
                     notes: Optional[str] = None,
                     deadline_hours: Optional[float] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a repair ticket.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            brand: Device brand
            model: Device model
            problem: Problem description
            
        Returns:
            (success, message, ticket_id)
        """
        # Ensure we have a valid token
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        
        # Match model casing with database to avoid duplicate issues
        model = self._get_case_matched_model(device_id, brand, model)
        
        now_local = london_now()
        hours = 24.0
        if deadline_hours is not None:
            try:
                hours = float(deadline_hours)
            except (ValueError, TypeError):
                hours = 24.0
        if hours <= 0:
            hours = 24.0
        deadline_local = now_local + timedelta(hours=hours)

        def to_iso(dt):
            return dt.isoformat(timespec="seconds")

        ticket_data = {
            "deviceBrand": brand,
            "deviceModel": model,
            "problemExplanation": problem,
            "status": "PENDING",
            "deviceLocation": "IN_THE_FRONT",
            "withClient": False,
            "client": None,
            "timestamp": to_iso(now_local),
            "deadline": to_iso(deadline_local),
            "customerRequest": problem or "",
            "deviceCondition": "",
            "devicePassword": "",
            "serialNumberOrImei": "",
            "accessories": "",
            "notes": "",
            "totalPrice": 0,  # Default to 0 (matches web interface behavior)
            "deposit": 0      # Default to 0 (matches web interface behavior)
        }
        
        # Override optional fields if provided
        if device_condition:
            ticket_data["deviceCondition"] = str(device_condition)
        if accessories:
            ticket_data["accessories"] = str(accessories)
        if total_price is not None:
            try:
                ticket_data["totalPrice"] = float(total_price)
            except (ValueError, TypeError):
                logger.warning(f"Invalid totalPrice: {total_price}, using 0")
        if deposit is not None:
            try:
                ticket_data["deposit"] = float(deposit)
            except (ValueError, TypeError):
                logger.warning(f"Invalid deposit: {deposit}, using 0")
        if device_password:
            ticket_data["devicePassword"] = str(device_password)  # API expects string
        if notes:
            ticket_data["notes"] = str(notes)  # API expects string
        
        # Make request
        logger.info(f"Creating ticket with data: {ticket_data}")
        response = self._make_request(
            device_id,
            "/YOUR_SHOP_API_PATH",
            method="POST",
            json_data=ticket_data
        )
        
        if response is None:
            logger.error(f"create_ticket: _make_request returned None for device {device_id}")
        else:
            logger.info(f"create_ticket: Got response status {response.status_code}")
            if response.status_code != 200:
                logger.error(f"❌ API Error Response:")
                logger.error(f"📋 Headers: {dict(response.headers)}")
                try:
                    error_json = response.json()
                    logger.error(f"📝 Body (JSON): {error_json}")
                except:
                    logger.error(f"📝 Body (text): {response.text[:500]}")
        
        # Handle 401 (token expired) - retry once
        if response and response.status_code == 401:
            logger.info(f"Token expired for device {device_id}, re-authenticating...")
            if self._login(device_id, username, password):
                response = self._make_request(
                    device_id,
                    "/YOUR_SHOP_API_PATH",
                    method="POST",
                    json_data=ticket_data
                )
        
        # Parse response
        logger.info(f"🔍 About to parse response: response is not None = {response is not None}")
        try:
            response_bool = bool(response)
            logger.info(f"🔍 bool(response) = {response_bool}")
        except Exception as e:
            logger.error(f"⚠️ Exception when calling bool(response): {e}")
            response_bool = False
        
        if response_bool:
            logger.info(f"🔍 Response type: {type(response)}, has status_code: {hasattr(response, 'status_code')}")
            try:
                logger.info(f"🔍 Response status_code: {response.status_code}")
            except Exception as e:
                logger.error(f"⚠️ Cannot access response.status_code: {e}")
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                ticket_id = result.get("id")
                if ticket_id:
                    logger.info(f"Created ticket {ticket_id} for device {device_id}")
                    due = deadline_local.strftime("%H:%M")
                    price_bit = ""
                    if ticket_data.get("totalPrice"):
                        price_bit = f", £{ticket_data['totalPrice']:.0f}"
                    return True, f"Ticket {ticket_id} booked{price_bit}, due {due}", ticket_id
                else:
                    logger.error(f"Ticket creation response missing ID. Response: {result}")
                    return False, "Ticket creation response missing ID", None
            except Exception as e:
                logger.error(f"Failed to parse ticket response: {e}. Response text: {response.text}")
                return False, "Failed to parse ticket response", None
        elif response:
            logger.error(f"❌ Ticket creation failed: HTTP {response.status_code}")
            logger.error(f"📋 Response headers: {dict(response.headers)}")
            logger.error(f"🔍 Attempting to parse error response...")
            try:
                error_body = response.json()
                logger.error(f"📝 Response body (JSON): {error_body}")
                error_msg = error_body.get('message', error_body.get('error', str(error_body)))
            except Exception as parse_error:
                logger.error(f"⚠️ Failed to parse JSON: {parse_error}")
                error_body = response.text[:500]
                logger.error(f"📝 Response body (text): {error_body}")
                error_msg = f"HTTP {response.status_code}"
            
            logger.error(f"💬 Final error message: {error_msg}")
            return False, f"Ticket creation failed: {error_msg}", None
        else:
            logger.error("❌ Ticket creation failed: No response received from API (response is None)")
            return False, "Failed to create ticket. Could not reach the ticketing system", None
    
    def create_invoice(self, device_id: str, username: str, password: str,
                      brand: str, model: str, total_price: float, 
                      serial_number: str, payment_method: str,
                      count: int = 1, warranty_period: str = "ONE_MONTH",
                      notes: str = "") -> Tuple[bool, str, Optional[str]]:
        """
        Create a sales invoice.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            brand: Device brand
            model: Device model
            total_price: Sale price
            serial_number: IMEI/serial number
            payment_method: CARD, CASH, or COMBINED
            count: Quantity
            warranty_period: Hatfield warranty enum or spoken form
            notes: Extra notes (storage, colour, spoken warranty)
            
        Returns:
            (success, message, invoice_id)
        """
        # Ensure we have a valid token
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        
        # Prepare invoice data
        now_utc = datetime.now(timezone.utc)
        timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        qty = int(count) if count else 1
        if qty < 1:
            qty = 1
        warranty = parse_warranty(warranty_period, default="ONE_MONTH")
        
        invoice_data = {
            "deviceBrand": brand,
            "deviceModel": model,
            "deviceName": f"{brand} {model}".strip(),
            "warrantyPeriod": warranty,
            "paymentMethod": payment_method.upper(),
            "type": "SELL",
            "count": qty,
            "timestamp": timestamp_str,
            "totalPrice": float(total_price),
            "serialNumber": serial_number or "",
            "notes": notes or "",
        }
        
        # Make request
        response = self._make_request(
            device_id,
            "/YOUR_SHOP_API_PATH",
            method="POST",
            json_data=invoice_data
        )
        
        # Handle 401 (token expired) - retry once
        if response and response.status_code == 401:
            logger.info(f"Token expired for device {device_id}, re-authenticating...")
            if self._login(device_id, username, password):
                response = self._make_request(
                    device_id,
                    "/YOUR_SHOP_API_PATH",
                    method="POST",
                    json_data=invoice_data
                )
        
        # Parse response
        if response and response.status_code == 200:
            # API returns invoice ID as plain text
            invoice_id = response.text.strip()
            if invoice_id:
                logger.info(f"Created invoice {invoice_id} for device {device_id}")
                return True, f"Invoice {invoice_id} created successfully", invoice_id
            else:
                return False, "Invoice creation response missing ID", None
        elif response:
            logger.error(f"Invoice creation failed: {response.status_code} - {response.text}")
            return False, f"Failed to create invoice (error {response.status_code})", None
        else:
            return False, "Failed to create invoice (network error)", None
    
    def download_invoice_pdf(self, device_id: str, invoice_id: str, 
                            output_dir: str) -> Optional[str]:
        """
        Download invoice PDF.
        
        Args:
            device_id: Device identifier
            invoice_id: Invoice ID to download
            output_dir: Directory to save PDF
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        token_info = self.device_tokens.get(device_id)
        if not token_info:
            logger.error(f"No token for device {device_id}")
            return None
        
        url = f"{self.BASE_URL}/YOUR_SHOP_API_PATH"
        headers = {
            "Authorization": f"Bearer {token_info['token']}",
            "Accept": "application/pdf"
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                params={"invoiceId": invoice_id},
                timeout=30
            )
            
            if response.status_code == 200:
                # Save PDF
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.join(output_dir, f"invoice_{invoice_id}.pdf")
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded invoice PDF: {filename}")
                return filename
            else:
                logger.error(f"PDF download failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"PDF download error: {e}")
            return None
    
    def get_ticket_status(self, device_id: str, username: str, password: str,
                         ticket_id: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Get ticket status.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            ticket_id: Ticket ID to query
            
        Returns:
            (success, message, ticket_data)
        """
        # Ensure we have a valid token
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        
        # Make request
        response = self._make_request(
            device_id,
            f"/YOUR_SHOP_API_PATH",
            method="GET",
            params={"id": ticket_id}
        )
        
        # Handle 401 (token expired) - retry once
        if response and response.status_code == 401:
            logger.info(f"Token expired for device {device_id}, re-authenticating...")
            if self._login(device_id, username, password):
                response = self._make_request(
                    device_id,
                    f"/YOUR_SHOP_API_PATH",
                    method="GET",
                    params={"id": ticket_id}
                )
        
        # Parse response
        if response and response.status_code == 200:
            ticket_data = response.json()
            logger.info(f"Retrieved ticket {ticket_id} for device {device_id}")
            
            # Format response
            status = ticket_data.get('status', 'Unknown')
            brand = ticket_data.get('deviceBrand', 'Unknown')
            model = ticket_data.get('deviceModel', 'Unknown')
            problem = ticket_data.get('problemExplanation', 'No description')
            
            message = f"Ticket {ticket_id}: {status}. Device: {brand} {model}. Problem: {problem}"
            return True, message, ticket_data
        elif response:
            logger.error(f"Ticket query failed: {response.status_code}")
            return False, f"Failed to get ticket status (error {response.status_code})", None
        else:
            return False, "Failed to get ticket status (network error)", None
    
    def update_ticket_status(self, device_id: str, username: str, password: str,
                            ticket_id: str, status_endpoint: str) -> Tuple[bool, str]:
        """
        Update ticket status (start, complete, freeze, cancel, etc.).
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            ticket_id: Ticket ID to update
            status_endpoint: Full endpoint with params (e.g., "/YOUR_SHOP_API_PATH?id=123")
            
        Returns:
            (success, message)
        """
        # Ensure we have a valid token
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop"
        
        # Make request
        response = self._make_request(
            device_id,
            status_endpoint,
            method="PUT"
        )
        
        # Handle 401 (token expired) - retry once
        if response and response.status_code == 401:
            logger.info(f"Token expired for device {device_id}, re-authenticating...")
            if self._login(device_id, username, password):
                response = self._make_request(
                    device_id,
                    status_endpoint,
                    method="PUT"
                )
        
        # Parse response
        if response and response.status_code == 200:
            logger.info(f"Updated ticket {ticket_id} status for device {device_id}")
            return True, f"Ticket {ticket_id} updated successfully"
        elif response:
            logger.error(f"Ticket status update failed: {response.status_code} - {response.text}")
            return False, f"Failed to update ticket (error {response.status_code})"
        else:
            return False, "Failed to update ticket (network error)"
    
    def print_ticket_document(self, device_id: str, username: str, password: str,
                             ticket_id: str, document_type: str = "ticket",
                             output_dir: str = "invoices") -> Tuple[bool, str, Optional[str]]:
        """
        Print ticket document (receipt or repair tag).
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            ticket_id: Ticket ID to print
            document_type: "tag"/"repair" for the device ticket label,
                           "ticket"/"customer" for the customer label
            output_dir: Directory to save PDF
            
        Returns:
            (success, message, pdf_path)
        """
        # Ensure we have a valid token
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        
        # Determine endpoint
        if document_type in ("tag", "repair"):
            document_type = "tag"
            endpoint = "/YOUR_SHOP_API_PATH"
        else:
            document_type = "customer"
            endpoint = "/YOUR_SHOP_API_PATH"
        
        token_info = self.device_tokens.get(device_id)
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token_info['token']}",
            "Accept": "application/pdf"
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                params={"ticketId": ticket_id},
                timeout=30
            )
            
            if response.status_code == 200:
                # Save PDF
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.join(output_dir, f"ticket_{ticket_id}_{document_type}.pdf")
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded ticket {document_type} PDF: {filename}")
                return True, f"Ticket {ticket_id} {document_type} ready to print", filename
            else:
                logger.error(f"PDF download failed: {response.status_code}")
                return False, f"Failed to generate {document_type} (error {response.status_code})", None
                
        except Exception as e:
            logger.error(f"PDF download error: {e}")
            return False, f"Failed to generate {document_type}", None
    
    def get_shop_tickets(self, device_id: str, username: str, password: str,
                         page_size: int = 20) -> Tuple[bool, str, Optional[list]]:
        """
        List tickets in the shop (GET /YOUR_SHOP_API_PATH), newest first.
        Falls back to GET /YOUR_SHOP_API_PATH if /all is unavailable.
        """
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None

        tickets: list = []
        total = None

        def _parse_tickets(payload) -> list:
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                for key in ("content", "tickets", "data", "items"):
                    val = payload.get(key)
                    if isinstance(val, list):
                        return val
            return []

        def _get(endpoint: str, params: Optional[dict] = None):
            response = self._make_request(device_id, endpoint, method="GET", params=params)
            if response and response.status_code == 401:
                logger.info(f"Token expired for device {device_id}, re-authenticating...")
                if self._login(device_id, username, password):
                    response = self._make_request(device_id, endpoint, method="GET", params=params)
            return response

        logger.info(f"GET /YOUR_SHOP_API_PATH pageSize={page_size} for device {device_id}")
        resp = _get("/YOUR_SHOP_API_PATH", {"page": 1, "pageSize": page_size, "size": page_size, "sort": "id,desc"})
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                tickets = _parse_tickets(data)
                if isinstance(data, dict):
                    total = data.get("totalCount") or data.get("total")
                logger.info(f"ticket/all returned {len(tickets)} tickets (total={total})")
            except Exception as e:
                logger.error(f"Failed to parse /YOUR_SHOP_API_PATH: {e}")
        elif resp:
            logger.warning(f"/YOUR_SHOP_API_PATH failed: {resp.status_code}")
        else:
            logger.warning("/YOUR_SHOP_API_PATH: no response")

        logger.info(f"GET /YOUR_SHOP_API_PATH for device {device_id}")
        active_resp = _get("/YOUR_SHOP_API_PATH")
        if active_resp and active_resp.status_code == 200:
            try:
                active = _parse_tickets(active_resp.json())
                seen = {t.get("id") for t in tickets}
                for t in active:
                    if t.get("id") not in seen:
                        tickets.append(t)
                logger.info(f"ticket/active merged, now {len(tickets)} tickets")
            except Exception as e:
                logger.error(f"Failed to parse /YOUR_SHOP_API_PATH: {e}")

        if not tickets:
            return True, "There are no tickets in the system.", []

        def _tid(t):
            try:
                return int(t.get("id") or 0)
            except (TypeError, ValueError):
                return 0

        tickets.sort(key=_tid, reverse=True)
        last = tickets[0]
        last_id = last.get("id", "?")
        brand = last.get("deviceBrand") or ""
        model = last.get("deviceModel") or ""
        problem = last.get("problemExplanation") or ""
        if "," in problem:
            problem = problem.split(",")[0]
        spoken = f"Last ticket is {last_id}, {brand} {model} for {problem}.".replace("  ", " ")
        extra = tickets[1:5]
        if extra:
            bits = [f"{t.get('id')} {t.get('deviceBrand', '')} {t.get('deviceModel', '')}".strip() for t in extra]
            spoken += " Also " + ", ".join(bits) + "."
        if total:
            spoken += f" {total} tickets in the system."
        logger.info(f"Shop tickets summary: {spoken}")
        return True, spoken, tickets

    def summarize_open_tickets(self, device_id: str, username: str, password: str,
                               limit: int = 5) -> Tuple[bool, str, Optional[list]]:
        """Count incomplete tickets from /active (merged) and name the newest few."""
        success, fallback, tickets = self.get_shop_tickets(device_id, username, password, page_size=20)
        if not success:
            return success, fallback, tickets
        open_t = []
        for t in tickets or []:
            st = (t.get("status") or "").upper()
            if st in INCOMPLETE_STATUSES or st == "":
                open_t.append(t)
        n = len(open_t)
        if n == 0:
            return True, "There are no open tickets right now.", []
        bits = []
        for t in open_t[:limit]:
            problem = (t.get("problemExplanation") or "").split(",")[0].strip()
            bits.append(
                f"{t.get('id')} {t.get('deviceBrand', '')} {t.get('deviceModel', '')} for {problem}".replace("  ", " ").strip()
            )
        msg = f"There are {n} open tickets. Newest: " + ", ".join(bits) + "."
        logger.info(f"Open tickets summary: {msg}")
        return True, msg, open_t

    def get_pending_tickets(self, device_id: str, username: str, password: str) -> Tuple[bool, str, Optional[list]]:
        """
        Get list of pending/active tickets.
        
        Args:
            device_id: Device identifier
            username: Phoneshop username
            password: Phoneshop password
            
        Returns:
            (success, message, tickets_list)
        """
        # Ensure we have a valid token
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        
        # Get shop ID from token info
        token_info = self.device_tokens.get(device_id)
        shop_id = token_info.get('shop_id') if token_info else None
        
        # Make request with filter for active/pending tickets
        params = {
            'status': 'PENDING,IN_PROGRESS',  # Filter for active tickets
            'page': 0,
            'size': 10,  # Get top 10 pending tickets
            'sort': 'id,asc'  # Oldest first
        }
        
        if shop_id:
            params['shopId'] = shop_id
        
        response = self._make_request(
            device_id,
            "/YOUR_SHOP_API_PATH",
            method="GET",
            params=params
        )
        
        # Handle 401 (token expired) - retry once
        if response and response.status_code == 401:
            logger.info(f"Token expired for device {device_id}, re-authenticating...")
            if self._login(device_id, username, password):
                response = self._make_request(
                    device_id,
                    "/YOUR_SHOP_API_PATH",
                    method="GET",
                    params=params
                )
        
        # Parse response
        if response and response.status_code == 200:
            try:
                tickets = response.json()
                
                if not tickets or len(tickets) == 0:
                    return True, "No pending tickets.", []
                
                # Format message: "123 iPhone 11 for screen, 124 iPhone 12 for charge port"
                formatted_lines = []
                for ticket in tickets:
                    ticket_id = ticket.get('id', 'Unknown')
                    brand = ticket.get('deviceBrand', '')
                    model = ticket.get('deviceModel', '')
                    problem = ticket.get('problemExplanation', '')
                    
                    # Extract just the main issue (before comma or period)
                    if ',' in problem:
                        problem = problem.split(',')[0]
                    if '.' in problem:
                        problem = problem.split('.')[0]
                    
                    formatted_lines.append(f"{ticket_id} {brand} {model} for {problem}")
                
                message = ", ".join(formatted_lines)
                logger.info(f"Retrieved {len(tickets)} pending tickets for device {device_id}")
                return True, message, tickets
                
            except Exception as e:
                logger.error(f"Failed to parse pending tickets: {e}")
                return False, "Failed to parse tickets list", None
        elif response:
            logger.error(f"Get pending tickets failed: {response.status_code}")
            return False, f"Failed to get pending tickets (error {response.status_code})", None
        else:
            return False, "Failed to get pending tickets (network error)", None

    def _shop_id(self, device_id: str):
        info = self.device_tokens.get(device_id) or {}
        return info.get("shop_id")

    def get_todays_bookings(self, device_id: str, username: str, password: str) -> Tuple[bool, str, Optional[list]]:
        """Tickets created today (London), split into incomplete vs done."""
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        day = london_now().strftime("%Y-%m-%d")
        shop_id = self._shop_id(device_id)
        tickets: list = []
        page = 1
        while page <= 10:
            params = {
                "createdAfter": day,
                "createdBefore": day,
                "page": page,
                "pageSize": 100,
            }
            if shop_id:
                params["shopId"] = shop_id
            resp = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="GET", params=params)
            if resp and resp.status_code == 401 and self._login(device_id, username, password):
                resp = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="GET", params=params)
            if not resp or resp.status_code != 200:
                break
            data = resp.json() if resp.content else {}
            batch = []
            if isinstance(data, list):
                batch = data
            elif isinstance(data, dict):
                batch = data.get("content") or data.get("tickets") or []
            tickets.extend(batch)
            page_count = data.get("pageCount") if isinstance(data, dict) else 1
            if not batch or page >= (page_count or 1):
                break
            page += 1

        def _status(t):
            return str(t.get("status") or "").upper()

        open_ones = [t for t in tickets if _status(t) in INCOMPLETE_STATUSES]
        done_ones = [t for t in tickets if _status(t) not in INCOMPLETE_STATUSES]

        def _line(t):
            tid = t.get("id", "?")
            brand = t.get("deviceBrand") or ""
            model = t.get("deviceModel") or ""
            problem = (t.get("problemExplanation") or t.get("customerRequest") or "").split(",")[0]
            st = _status(t).replace("_", " ").title()
            return f"{tid} {brand} {model} {problem} ({st})".replace("  ", " ").strip()

        if not tickets:
            return True, "Nothing was booked today.", []

        parts = [f"{len(tickets)} booked today."]
        if open_ones:
            parts.append("Still not completed: " + "; ".join(_line(t) for t in open_ones[:8]) + ".")
        else:
            parts.append("Everything booked today is completed.")
        if done_ones:
            parts.append("Already done: " + "; ".join(_line(t) for t in done_ones[:6]) + ".")
        spoken = " ".join(parts)
        logger.info("Today bookings: %s", spoken)
        return True, spoken, tickets

    def create_inventory_item(self, device_id: str, username: str, password: str,
                              name: str, purchase_price: float, sell_price: float,
                              brand: str = "", model: str = "", imei: str = "",
                              count: int = 1) -> Tuple[bool, str, Optional[int]]:
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        shop_id = self._shop_id(device_id)
        body = {
            "id": None,
            "name": name,
            "imei": imei or "",
            "purchasePrice": float(purchase_price),
            "sellPrice": float(sell_price),
            "model": model or None,
            "modelId": None,
            "brand": brand or None,
            "brandId": None,
            "count": int(count) if count else 1,
            "shopId": shop_id,
            "categoryId": None,
            "properties": {},
        }
        resp = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="POST", json_data=body)
        if resp and resp.status_code == 401 and self._login(device_id, username, password):
            resp = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="POST", json_data=body)
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                item_id = data.get("id") if isinstance(data, dict) else None
            except Exception:
                item_id = None
            msg = f"Added {name} to inventory"
            if imei:
                msg += f", IMEI {imei}"
            msg += f", cost £{float(purchase_price):.0f}, price £{float(sell_price):.0f}"
            if item_id:
                msg += f". Item {item_id}"
            return True, msg, item_id
        err = resp.text[:200] if resp is not None else "network error"
        code = resp.status_code if resp is not None else 0
        logger.error("inventory create failed %s %s", code, err)
        return False, f"Failed to add inventory (error {code})", None

    def create_accessories_invoice(self, device_id: str, username: str, password: str,
                                   device_name: str, total_price: float, count: int = 1,
                                   payment_method: str = "CASH",
                                   notes: str = "",
                                   warranty_period: str = "NONE") -> Tuple[bool, str, Optional[str]]:
        if not self._ensure_token(device_id, username, password):
            return False, "Failed to authenticate with Phoneshop", None
        now_local = london_now()
        qty = int(count) if count else 1
        if qty < 1:
            qty = 1
        body = {
            "type": "ACCESSORIES",
            "deviceName": device_name,
            "serialNumber": "-",
            "count": qty,
            "timestamp": now_local.isoformat(timespec="seconds"),
            "totalPrice": float(total_price),
            "paymentMethod": (payment_method or "CASH").upper(),
            "warrantyPeriod": parse_warranty(warranty_period, default="NONE"),
            "notes": notes or f"{qty} {device_name}",
        }
        resp = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="POST", json_data=body)
        if resp and resp.status_code == 401 and self._login(device_id, username, password):
            resp = self._make_request(device_id, "/YOUR_SHOP_API_PATH", method="POST", json_data=body)
        if resp and resp.status_code == 200:
            invoice_id = resp.text.strip().strip('"')
            if invoice_id:
                return True, f"Invoice {invoice_id} created for {count} {device_name}, £{float(total_price):.0f}", invoice_id
            return False, "Invoice creation response missing ID", None
        err = resp.text[:200] if resp is not None else "network error"
        code = resp.status_code if resp is not None else 0
        logger.error("accessories invoice failed %s %s", code, err)
        return False, f"Failed to create invoice (error {code})", None


def print_pdf_windows(filename: str) -> bool:
    """
    Print PDF on Windows using default printer.
    
    Args:
        filename: Path to PDF file
        
    Returns:
        True if print successful, False otherwise
    """
    try:
        from win32 import win32print, win32api
        
        printer_name = win32print.GetDefaultPrinter()
        win32api.ShellExecute(
            0,
            "print",
            filename,
            f'/d:"{printer_name}"',
            ".",
            0
        )
        logger.info(f"Sent PDF to printer: {printer_name}")
        return True
        
    except ImportError:
        logger.warning("pywin32 not installed - cannot print PDF")
        return False
    except Exception as e:
        logger.error(f"Print error: {e}")
        return False


def open_pdf_windows(filename: str) -> bool:
    """Open a PDF with the default app on this computer."""
    path = os.path.abspath(filename)
    if not os.path.isfile(path):
        logger.error(f"PDF not found: {path}")
        return False
    try:
        os.startfile(path)
        logger.info(f"Opened PDF on computer: {path}")
        return True
    except OSError as e:
        logger.warning(f"os.startfile failed ({e}), trying explorer")
        try:
            import subprocess
            subprocess.Popen(["explorer", path], close_fds=True)
            logger.info(f"Opened PDF via explorer: {path}")
            return True
        except Exception as e2:
            logger.error(f"Failed to open PDF: {e2}")
            return False
    except Exception as e:
        logger.error(f"Failed to open PDF: {e}")
        return False


def print_or_open_pdf(filename: str) -> str:
    """Print the PDF; if that fails, open it on the computer.

    Returns:
        'printed', 'opened', or 'failed'
    """
    if print_pdf_windows(filename):
        return "printed"
    logger.warning("Print failed, opening PDF on the computer instead")
    if open_pdf_windows(filename):
        return "opened"
    return "failed"
