-- Drop all existing policies first
DROP POLICY IF EXISTS view_purchase_requests ON public.purchase_requests;
DROP POLICY IF EXISTS create_purchase_requests ON public.purchase_requests;
DROP POLICY IF EXISTS update_purchase_requests ON public.purchase_requests;
DROP POLICY IF EXISTS delete_purchase_requests ON public.purchase_requests;
DROP POLICY IF EXISTS "Users can view their own purchase requests" ON public.purchase_requests;
DROP POLICY IF EXISTS "Users can view their own requests and Finance/Admin can view al" ON public.purchase_requests;
DROP POLICY IF EXISTS "Users can create their own purchase requests" ON public.purchase_requests;
DROP POLICY IF EXISTS "Users can create their own requests" ON public.purchase_requests;
DROP POLICY IF EXISTS "Users can update their own draft or pending purchase requests" ON public.purchase_requests;
DROP POLICY IF EXISTS "Only Finance and Admin can update requests" ON public.purchase_requests;
DROP POLICY IF EXISTS "Admins and finance can update any purchase request" ON public.purchase_requests;

-- Drop item policies
DROP POLICY IF EXISTS view_purchase_request_items ON public.purchase_request_items;
DROP POLICY IF EXISTS create_purchase_request_items ON public.purchase_request_items;
DROP POLICY IF EXISTS update_purchase_request_items ON public.purchase_request_items;
DROP POLICY IF EXISTS delete_purchase_request_items ON public.purchase_request_items;
DROP POLICY IF EXISTS "Users can view items of visible purchase requests" ON public.purchase_request_items;
DROP POLICY IF EXISTS "Users can view items of their requests and Finance/Admin can vi" ON public.purchase_request_items;
DROP POLICY IF EXISTS "Users can create items for their own purchase requests" ON public.purchase_request_items;
DROP POLICY IF EXISTS "Users can update items of their own draft or pending purchase r" ON public.purchase_request_items;
DROP POLICY IF EXISTS "Admins and finance can update any purchase request items" ON public.purchase_request_items;

-- Policies for purchase_requests table
ALTER TABLE public.purchase_requests ENABLE ROW LEVEL SECURITY;

-- Policy for viewing PRFs
CREATE POLICY view_purchase_requests ON public.purchase_requests
    FOR SELECT
    TO authenticated
    USING (
        auth.uid() = requestor_id -- Can view own PRFs
        OR 
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() 
            AND role IN ('Finance', 'Admin')
        )
    );

-- Policy for creating PRFs
CREATE POLICY create_purchase_requests ON public.purchase_requests
    FOR INSERT
    TO authenticated
    WITH CHECK (
        auth.uid() = requestor_id
        AND EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid()
        )
    );

-- Policy for updating PRFs
CREATE POLICY update_purchase_requests ON public.purchase_requests
    FOR UPDATE
    TO authenticated
    USING (
        (
            auth.uid() = requestor_id 
            AND (
                status IN ('draft', 'pending')  -- Allow updates for draft/pending
                OR (status IS NULL)  -- Allow initial creation
            )
        )
        OR 
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() 
            AND role IN ('Finance', 'Admin')  -- Finance/Admin can update any status
        )
    );

-- Policy for deleting PRFs
CREATE POLICY delete_purchase_requests ON public.purchase_requests
    FOR DELETE
    TO authenticated
    USING (
        (
            auth.uid() = requestor_id 
            AND status = 'draft'
        )  -- Can only delete own drafts
        OR 
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() 
            AND role = 'Admin'  -- Only Admin can delete any
        )
    );

-- Policies for purchase_request_items table
ALTER TABLE public.purchase_request_items ENABLE ROW LEVEL SECURITY;

-- Policy for viewing items
CREATE POLICY view_purchase_request_items ON public.purchase_request_items
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.purchase_requests pr
            WHERE pr.id = purchase_request_id
            AND (
                pr.requestor_id = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM public.profiles
                    WHERE id = auth.uid()
                    AND role IN ('Finance', 'Admin')
                )
            )
        )
    );

-- Policy for creating items
CREATE POLICY create_purchase_request_items ON public.purchase_request_items
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.purchase_requests pr
            WHERE pr.id = purchase_request_id
            AND pr.requestor_id = auth.uid()
            AND (
                pr.status IN ('draft', 'pending')
                OR pr.status IS NULL
            )
        )
    );

-- Policy for updating items
CREATE POLICY update_purchase_request_items ON public.purchase_request_items
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.purchase_requests pr
            WHERE pr.id = purchase_request_id
            AND (
                (
                    pr.requestor_id = auth.uid() 
                    AND (
                        pr.status IN ('draft', 'pending')
                        OR pr.status IS NULL
                    )
                )
                OR EXISTS (
                    SELECT 1 FROM public.profiles
                    WHERE id = auth.uid()
                    AND role IN ('Finance', 'Admin')
                )
            )
        )
    );

-- Policy for deleting items
CREATE POLICY delete_purchase_request_items ON public.purchase_request_items
    FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.purchase_requests pr
            WHERE pr.id = purchase_request_id
            AND (
                (
                    pr.requestor_id = auth.uid() 
                    AND pr.status = 'draft'
                )
                OR EXISTS (
                    SELECT 1 FROM public.profiles
                    WHERE id = auth.uid()
                    AND role = 'Admin'
                )
            )
        )
    );
