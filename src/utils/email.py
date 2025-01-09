from mailjet_rest import Client
from typing import List
import os

class EmailNotifier:
    def __init__(self):
        self.mailjet = Client(
            auth=(os.getenv('MAILJET_API_KEY'), 
                  os.getenv('MAILJET_API_SECRET')),
            version='v3.1'
        )
    
    async def send_prof_notification(
        self,
        prof_data: dict,
        recipients: List[dict]
    ) -> None:
        """Send email notification for new PROF submission"""
        try:
            data = {
                'Messages': [{
                    'From': {
                        'Email': "finance@vivitaphilippines.org",
                        'Name': "VIVITA Finance"
                    },
                    'To': recipients,
                    'Subject': f"New PROF #{prof_data['form_number']} Requires Approval",
                    'TextPart': self._generate_prof_email_text(prof_data),
                    'HTMLPart': self._generate_prof_email_html(prof_data)
                }]
            }
            
            response = await self.mailjet.send.create(data=data)
            if response.status_code != 200:
                raise Exception(f"Failed to send email: {response.text}")
                
        except Exception as e:
            print(f"Error sending email notification: {str(e)}")
    
    def _generate_prof_email_html(self, prof_data: dict) -> str:
        items_html = "".join([
            f"<tr><td>{item['item_description']}</td>"
            f"<td>{item['quantity']} {item['unit']}</td>"
            f"<td>₱{float(item['unit_price']):,.2f}</td>"
            f"<td>₱{float(item['quantity']) * float(item['unit_price']):,.2f}</td></tr>"
            for item in prof_data['items']
        ])
        
        return f"""
        <h2>New Purchase Request Requires Your Approval</h2>
        <p>PROF #{prof_data['form_number']} has been submitted and requires your approval.</p>
        
        <h3>Details:</h3>
        <ul>
            <li><strong>Requestor:</strong> {prof_data['requestor']}</li>
            <li><strong>Department:</strong> {prof_data['department']}</li>
            <li><strong>Supplier:</strong> {prof_data['supplier']}</li>
            <li><strong>Date:</strong> {prof_data['date']}</li>
            <li><strong>Total Amount:</strong> ₱{prof_data['total_amount']:,.2f}</li>
        </ul>
        
        <h3>Items:</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Amount</th>
            </tr>
            {items_html}
        </table>
        
        <p>Please review and process this request as soon as possible.</p>
        <p><a href="{self._get_approval_url(prof_data['form_number'])}">Click here to review</a></p>
        """
    
    def _generate_prof_email_text(self, prof_data: dict) -> str:
        items_text = "\n".join([
            f"- {item['item_description']}: "
            f"{item['quantity']} {item['unit']} x ₱{float(item['unit_price']):,.2f} = "
            f"₱{float(item['quantity']) * float(item['unit_price']):,.2f}"
            for item in prof_data['items']
        ])
        
        return f"""
        New Purchase Request Requires Your Approval

        PROF #{prof_data['form_number']} has been submitted and requires your approval.

        Details:
        - Requestor: {prof_data['requestor']}
        - Department: {prof_data['department']}
        - Supplier: {prof_data['supplier']}
        - Date: {prof_data['date']}
        - Total Amount: ₱{prof_data['total_amount']:,.2f}

        Items:
        {items_text}

        Please review and process this request as soon as possible.
        """
    
    def _get_approval_url(self, form_number: str) -> str:
        """Generate URL for approving the PROF"""
        # TODO: Replace with actual URL when deployment details are known
        return f"https://vivita-finance.streamlit.app/approve/{form_number}"
