-- Create purchase requests table
create table public.purchase_requests (
    id uuid not null default extensions.uuid_generate_v4(),
    form_number text not null,
    requestor_id uuid not null,
    supplier_id uuid not null,
    status text not null default 'draft'::text,
    total_amount numeric(15, 2) null,
    remarks text null,
    created_at timestamp with time zone not null default timezone('utc'::text, now()),
    updated_at timestamp with time zone not null default timezone('utc'::text, now()),
    constraint purchase_requests_pkey primary key (id),
    constraint purchase_requests_form_number_key unique (form_number),
    constraint purchase_requests_requestor_id_fkey foreign key (requestor_id) references auth.users (id),
    constraint purchase_requests_supplier_id_fkey foreign key (supplier_id) references suppliers (id),
    constraint purchase_requests_status_check check (
        status = any (array['draft'::text, 'pending'::text, 'approved'::text, 'rejected'::text])
    )
) tablespace pg_default;

-- Create trigger for updated_at
create trigger update_purchase_requests_updated_at 
    before update on purchase_requests 
    for each row execute function update_updated_at_column();

-- Create purchase request items table
create table public.purchase_request_items (
    id uuid not null default extensions.uuid_generate_v4(),
    purchase_request_id uuid not null,
    item_description text not null,
    quantity numeric(15, 2) not null,
    unit text not null,
    unit_price numeric(15, 2) not null,
    total_price numeric(15, 2) not null,
    account_code text null,
    remarks text null,
    created_at timestamp with time zone not null default timezone('utc'::text, now()),
    updated_at timestamp with time zone not null default timezone('utc'::text, now()),
    constraint purchase_request_items_pkey primary key (id),
    constraint purchase_request_items_purchase_request_id_fkey 
        foreign key (purchase_request_id) references purchase_requests (id) on delete cascade
) tablespace pg_default;

-- Create trigger for updated_at
create trigger update_purchase_request_items_updated_at 
    before update on purchase_request_items 
    for each row execute function update_updated_at_column();
