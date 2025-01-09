-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own purchase requests" ON purchase_requests;
DROP POLICY IF EXISTS "Users can create their own purchase requests" ON purchase_requests;
DROP POLICY IF EXISTS "Users can update their own pending purchase requests" ON purchase_requests;
DROP POLICY IF EXISTS "Admins and finance can update any purchase request" ON purchase_requests;
DROP POLICY IF EXISTS "Users can view items of visible purchase requests" ON purchase_request_items;
DROP POLICY IF EXISTS "Users can create items for their own purchase requests" ON purchase_request_items;
DROP POLICY IF EXISTS "Users can update items of their own pending purchase requests" ON purchase_request_items;
DROP POLICY IF EXISTS "Admins and finance can update any purchase request items" ON purchase_request_items;
DROP POLICY IF EXISTS "Users can view their own expense forms" ON expense_reimbursement_forms;
DROP POLICY IF EXISTS "Users can create their own expense forms" ON expense_reimbursement_forms;
DROP POLICY IF EXISTS "Users can update their own pending expense forms" ON expense_reimbursement_forms;
DROP POLICY IF EXISTS "Admins and finance can update any expense form" ON expense_reimbursement_forms;
DROP POLICY IF EXISTS "Users can view items of visible expense forms" ON expense_items;
DROP POLICY IF EXISTS "Users can create items for their own expense forms" ON expense_items;
DROP POLICY IF EXISTS "Users can update items of their own pending expense forms" ON expense_items;
DROP POLICY IF EXISTS "Admins and finance can update any expense items" ON expense_items;

-- Enable RLS on tables
ALTER TABLE purchase_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_request_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE expense_reimbursement_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE expense_items ENABLE ROW LEVEL SECURITY;

-- Purchase Requests Policies
CREATE POLICY "Users can view their own purchase requests"
    ON purchase_requests
    FOR SELECT
    USING (
        auth.uid()::uuid = requestor_id OR
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
        )
    );

CREATE POLICY "Users can create their own purchase requests"
    ON purchase_requests
    FOR INSERT
    WITH CHECK (
        auth.uid()::uuid = requestor_id AND
        (
            status = 'draft' OR
            status = 'pending'
        )
    );

CREATE POLICY "Users can update their own draft or pending purchase requests"
    ON purchase_requests
    FOR UPDATE
    USING (
        auth.uid()::uuid = requestor_id AND
        (
            status = 'draft' OR
            status = 'pending'
        )
    );

CREATE POLICY "Admins and finance can update any purchase request"
    ON purchase_requests
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
        )
    );

-- Purchase Request Items Policies
CREATE POLICY "Users can view items of visible purchase requests"
    ON purchase_request_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purchase_requests pr
            WHERE pr.id = purchase_request_items.purchase_request_id AND
            (pr.requestor_id = auth.uid()::uuid OR
             EXISTS (
                SELECT 1 FROM profiles p
                WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
             ))
        )
    );

CREATE POLICY "Users can create items for their own purchase requests"
    ON purchase_request_items
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM purchase_requests pr
            WHERE pr.id = purchase_request_id AND 
            pr.requestor_id = auth.uid()::uuid AND
            (
                pr.status = 'draft' OR
                pr.status = 'pending'
            )
        )
    );

CREATE POLICY "Users can update items of their own draft or pending purchase requests"
    ON purchase_request_items
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM purchase_requests pr
            WHERE pr.id = purchase_request_id AND
            pr.requestor_id = auth.uid()::uuid AND
            (
                pr.status = 'draft' OR
                pr.status = 'pending'
            )
        )
    );

CREATE POLICY "Admins and finance can update any purchase request items"
    ON purchase_request_items
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
        )
    );

-- Expense Reimbursement Forms Policies
CREATE POLICY "Users can view their own expense forms"
    ON expense_reimbursement_forms
    FOR SELECT
    USING (
        auth.uid()::uuid = employee_id OR
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
        )
    );

CREATE POLICY "Users can create their own expense forms"
    ON expense_reimbursement_forms
    FOR INSERT
    WITH CHECK (
        auth.uid()::uuid = employee_id AND
        (
            status = 'draft' OR
            status = 'pending'
        )
    );

CREATE POLICY "Users can update their own draft or pending expense forms"
    ON expense_reimbursement_forms
    FOR UPDATE
    USING (
        auth.uid()::uuid = employee_id AND
        (
            status = 'draft' OR
            status = 'pending'
        )
    );

CREATE POLICY "Admins and finance can update any expense form"
    ON expense_reimbursement_forms
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
        )
    );

-- Expense Items Policies
CREATE POLICY "Users can view items of visible expense forms"
    ON expense_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM expense_reimbursement_forms erf
            WHERE erf.id = expense_items.erf_id AND
            (erf.employee_id = auth.uid()::uuid OR
             EXISTS (
                SELECT 1 FROM profiles p
                WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
             ))
        )
    );

CREATE POLICY "Users can create items for their own expense forms"
    ON expense_items
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM expense_reimbursement_forms erf
            WHERE erf.id = erf_id AND 
            erf.employee_id = auth.uid()::uuid AND
            (
                erf.status = 'draft' OR
                erf.status = 'pending'
            )
        )
    );

CREATE POLICY "Users can update items of their own draft or pending expense forms"
    ON expense_items
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM expense_reimbursement_forms erf
            WHERE erf.id = erf_id AND
            erf.employee_id = auth.uid()::uuid AND
            (
                erf.status = 'draft' OR
                erf.status = 'pending'
            )
        )
    );

CREATE POLICY "Admins and finance can update any expense items"
    ON expense_items
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid() AND p.role IN ('Finance', 'Admin')
        )
    );
