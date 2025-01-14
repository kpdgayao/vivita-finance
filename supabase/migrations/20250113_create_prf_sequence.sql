-- Create sequence for PRF numbers
CREATE SEQUENCE IF NOT EXISTS prf_number_seq;

-- Create function to generate PRF numbers using sequence
CREATE OR REPLACE FUNCTION generate_prf_number()
RETURNS text
LANGUAGE plpgsql
AS $$
DECLARE
    year text := to_char(current_date, 'YYYY');
    next_num text;
BEGIN
    -- Get next value from sequence
    next_num := to_char(nextval('prf_number_seq'), 'FM0000');
    
    -- Return formatted PRF number
    RETURN 'PRF-' || year || '-' || next_num;
END;
$$;
