-- Create function to generate PRF numbers atomically
CREATE OR REPLACE FUNCTION get_next_prf_number(current_year text)
RETURNS TABLE (form_number text)
LANGUAGE plpgsql
AS $$
DECLARE
    latest_num integer;
    new_num integer;
BEGIN
    -- Lock the table to prevent concurrent access
    LOCK TABLE purchase_requests IN SHARE MODE;
    
    -- Get the latest number for this year
    SELECT COALESCE(
        MAX(CAST(SPLIT_PART(form_number, '-', 3) AS integer)),
        0
    )
    INTO latest_num
    FROM purchase_requests
    WHERE form_number LIKE 'PRF-' || current_year || '-%';
    
    -- Increment the number
    new_num := latest_num + 1;
    
    -- Return the new form number
    RETURN QUERY SELECT 'PRF-' || current_year || '-' || LPAD(new_num::text, 4, '0');
END;
$$;
