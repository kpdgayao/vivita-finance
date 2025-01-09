-- Disable RLS on all tables for now
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers DISABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_request_items DISABLE ROW LEVEL SECURITY;

-- Later, we can add proper RLS policies:
/*
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_request_items ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Enable read access for all users" ON users
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for service role" ON users
    FOR INSERT
    WITH CHECK (true);

-- Create policies for suppliers table
CREATE POLICY "Enable read access for all users" ON suppliers
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for authenticated users" ON suppliers
    FOR INSERT
    WITH CHECK (true);

-- Create policies for purchase_requests table
CREATE POLICY "Enable read access for all users" ON purchase_requests
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for authenticated users" ON purchase_requests
    FOR INSERT
    WITH CHECK (true);

-- Create policies for purchase_request_items table
CREATE POLICY "Enable read access for all users" ON purchase_request_items
    FOR SELECT
    USING (true);

CREATE POLICY "Enable insert for authenticated users" ON purchase_request_items
    FOR INSERT
    WITH CHECK (true);
*/
