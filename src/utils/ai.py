from anthropic import Anthropic
import asyncio
from typing import Dict, List
import os

class AccountClassifier:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.chart_of_accounts = self._load_chart_of_accounts()
    
    def _load_chart_of_accounts(self) -> Dict[str, List[Dict]]:
        """Load and structure the chart of accounts for easy reference."""
        # TODO: Load this from a configuration file or database
        return {
            'Expense': [
                {'code': '6011', 'name': 'Activity Expenses', 'description': 'For program and activity-related costs'},
                {'code': '6008', 'name': 'Supplies Expense', 'description': 'For office and learning supplies'},
                {'code': '6009', 'name': 'Professional Fees', 'description': 'For consulting and professional services'},
                {'code': '6010', 'name': 'Communication Expenses', 'description': 'For internet, phone, and communication costs'},
                {'code': '6005', 'name': 'Transportation Expenses', 'description': 'For local transport and delivery'},
                {'code': '6006', 'name': 'Accommodation & Travel Expenses', 'description': 'For travel-related expenses'},
                {'code': '6007', 'name': 'Website and Systems Development Cost', 'description': 'For IT and development expenses'},
                {'code': '6013', 'name': 'Subscriptions and Software Licenses', 'description': 'For software and subscription services'},
                {'code': '6100', 'name': 'Training and Related Expenses', 'description': 'For training and development costs'},
                {'code': '6015', 'name': 'Utilities Expense', 'description': 'For electricity, water, etc.'},
                {'code': '7100', 'name': 'Miscellaneous Expenses', 'description': 'For other expenses not fitting above categories'}
            ]
        }

    async def classify_expense(self, description: str, amount: float) -> dict:
        """Classify expense into appropriate accounting categories."""
        expense_accounts = "\n".join([
            f"- {account['name']} ({account['code']}): {account['description']}"
            for account in self.chart_of_accounts['Expense']
        ])
        
        prompt = f"""As an accounting expert, please classify the following expense based on VIVITA Philippines' chart of accounts:

Description: {description}
Amount: ₱{amount:,.2f}

The expense should be classified into one of these specific expense accounts:
{expense_accounts}

Please provide:
1. The most appropriate account code and name
2. Justification for the classification
3. Any tax considerations (e.g., withholding tax requirements)
4. Any additional notes for proper documentation

Format the response as:
Account Code: [code]
Account Name: [name]
Justification: [1-2 sentences explaining why this classification is appropriate]
Tax Notes: [any relevant tax considerations]
Documentation: [any additional documentation requirements]"""

        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=250,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return self._parse_classification(response.content)
    
    def _parse_classification(self, response: str) -> dict:
        """Parse Claude's response into structured classification data."""
        lines = response.strip().split('\n')
        classification = {}
        current_key = None
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key in ['Account Code', 'Account Name', 'Justification', 
                          'Tax Notes', 'Documentation']:
                    current_key = key
                    classification[key] = value
            elif current_key and line.strip():
                # Append additional lines to the current key's value
                classification[current_key] += ' ' + line.strip()
        
        return classification

    async def suggest_account_mappings(self, items: List[dict]) -> List[dict]:
        """Suggest account classifications for multiple items in a PROF."""
        classified_items = []
        
        for item in items:
            amount = float(item['price']) * float(item['quantity'])
            classification = await self.classify_expense(item['description'], amount)
            
            classified_items.append({
                **item,
                'account_code': classification['Account Code'],
                'account_name': classification['Account Name'],
                'classification_notes': classification['Justification']
            })
        
        return classified_items
