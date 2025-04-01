from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager
from utils import logger


async def check_double(worksheet, data):
    """
    Check if a user already exists in the spreadsheet
    """
    all_data = await worksheet.get_all_values()
    if all_data[0]:
        for row in all_data:
            if row[0] == data[0]:
                logger.info('A client with this id already exists in the table')
                return

    return True


async def get_sheet_url(spreadsheet, worksheet):
    """
    Get URL to specific sheet in spreadsheet
    """
    base_url = spreadsheet.url
    sheet_id = worksheet.id
    return f"{base_url}#gid={sheet_id}"


class SheetsService:
    def __init__(self):
        """Initialize the Google Sheets service"""
        self.agcm = AsyncioGspreadClientManager(self.get_creds)
        self.table_id = '15WId5XbvK1tohcmqNFg7k0QwMjw7p9E1bdeAm72EXME'

    @staticmethod
    def get_creds():
        """
        Get Google API credentials
        """
        creds = Credentials.from_service_account_file("nodepressionbot-59c72a15d0fd.json")
        return creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets"])

    async def save_user_to_sheets(self, user_data):
        """
        Save user information to Google Sheets
        """
        try:
            client = await self.agcm.authorize()
            table = await client.open_by_key(self.table_id)
            sheet = await table.get_sheet1()

            # Prepare row data
            row_data = [
                user_data["id"],
                user_data["first_name"],
                user_data["last_name"],
                user_data["username"],
                user_data["url"],
                user_data["datetime"],
                ""
            ]

            # Append new row if user doesn't exist
            if await check_double(sheet, row_data):
                await sheet.append_row(row_data)
                logger.info(
                    f"User {user_data['id']}, first_name: {user_data['first_name']}, last_name: {user_data['last_name']}, username: {user_data['username']}, url: {user_data['url']}")
                await self._create_history_sheet(table, user_data["id"])
            return True

        except Exception as e:
            logger.info(f"Error saving user to Google Sheets: {e}")
            return False

    async def get_all_users_from_sheets(self):
        """
        Get all user IDs from Google Sheets
        """
        try:
            client = await self.agcm.authorize()
            table = await client.open_by_key(self.table_id)
            sheet = await table.get_sheet1()

            # Get all values from the sheet
            all_data = await sheet.get_all_values()

            # Skip header row and get user IDs from first column
            user_ids = [row[0] for row in all_data[1:] if row]  # Skip header, ensure row isn't empty

            return user_ids
        except Exception as e:
            logger.error(f"Error fetching users from Google Sheets: {e}")
            return []

    async def _create_history_sheet(self, spreadsheet, user_id):
        """
        Create a new sheet for user message history
        """
        try:
            # Try to get existing sheet or create new one
            try:
                worksheet = await spreadsheet.worksheet(str(user_id))
                logger.info(f"History sheet for user {user_id} already exists")
            except:
                worksheet = await spreadsheet.add_worksheet(str(user_id), rows=1000, cols=4)
                # Add headers
                await worksheet.update('A1:D1', [['Timestamp', 'From', 'Message', 'Score']])
                logger.info(f"Created new history sheet for user {user_id}")

            # Update main sheet with history link
            main_sheet = await spreadsheet.get_worksheet(0)
            history_url = f"{spreadsheet.url}/edit#gid={worksheet.id}"

            # Find user's row and update link
            all_values = await main_sheet.get_all_values()
            for idx, row in enumerate(all_values):
                if row[0] == str(user_id):
                    cell_range = f'G{idx + 1}'
                    await main_sheet.update(cell_range, [[f'=HYPERLINK("{history_url}"; "История сообщений")']],
                                            value_input_option='USER_ENTERED')
                    logger.info(f"Updated history link for user {user_id}")
                    break

            return worksheet

        except Exception as e:
            logger.error(f"Error creating history sheet: {e}")
            return None

    async def save_message_history(self, user_id, from_user, message_text, score=None):
        """
        Save message to user's history sheet
        """
        try:
            client = await self.agcm.authorize()
            spreadsheet = await client.open_by_key(self.table_id)

            # Get or create history sheet
            try:
                history_sheet = await spreadsheet.worksheet(str(user_id))
            except:
                history_sheet = await self._create_history_sheet(spreadsheet, user_id)

            if not history_sheet:
                raise Exception("Could not access or create history sheet")

            # Prepare message data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row_data = [timestamp, from_user, message_text, score]

            # Append message to history
            await history_sheet.append_row(row_data)
            logger.info(f"Saved message to history for user {user_id} in Google Sheets")

        except Exception as e:
            logger.error(f"Error saving message history in Google Sheets: {e}")
