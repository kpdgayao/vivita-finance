from datetime import datetime
from uuid import UUID
from ..models.supplier import Supplier
from ..database import get_supabase_client

class SupplierManager:
    def __init__(self):
        self.supabase = get_supabase_client()

    def create(self, supplier: Supplier) -> Supplier:
        """Create a new supplier."""
        data = {
            'name': supplier.name,
            'contact_person': supplier.contact_person,
            'phone': supplier.phone,
            'email': supplier.email,
            'address': supplier.address,
            'tax_id': supplier.tax_id,
            'preferred_payment_method': supplier.preferred_payment_method,
            'bank_details': supplier.bank_details,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('suppliers').insert(data).execute()
        created_supplier = result.data[0]
        return Supplier(**created_supplier)

    def update(self, supplier: Supplier) -> Supplier:
        """Update an existing supplier."""
        if not supplier.id:
            raise ValueError("Supplier ID is required for update")

        data = {
            'name': supplier.name,
            'contact_person': supplier.contact_person,
            'phone': supplier.phone,
            'email': supplier.email,
            'address': supplier.address,
            'tax_id': supplier.tax_id,
            'preferred_payment_method': supplier.preferred_payment_method,
            'bank_details': supplier.bank_details,
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('suppliers').update(data).eq('id', str(supplier.id)).execute()
        updated_supplier = result.data[0]
        return Supplier(**updated_supplier)

    def delete(self, supplier_id: UUID) -> bool:
        """Delete a supplier by ID."""
        result = self.supabase.table('suppliers').delete().eq('id', str(supplier_id)).execute()
        return len(result.data) > 0

    def get(self, supplier_id: UUID) -> Supplier:
        """Get a supplier by ID."""
        result = self.supabase.table('suppliers').select('*').eq('id', str(supplier_id)).execute()
        if not result.data:
            return None
        return Supplier(**result.data[0])

    def list(self, search_query: str = None) -> list[Supplier]:
        """List all suppliers, optionally filtered by search query."""
        query = self.supabase.table('suppliers').select('*')
        
        if search_query:
            query = query.or_(f"name.ilike.%{search_query}%,contact_person.ilike.%{search_query}%")
            
        result = query.execute()
        return [Supplier(**item) for item in result.data]
