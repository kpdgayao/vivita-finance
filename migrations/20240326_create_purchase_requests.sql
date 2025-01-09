-- Create purchase_requests table
create table if not exists purchase_requests (
    id uuid default uuid_generate_v4() primary key,
    form_number text unique not null,
    requestor_id uuid references auth.users(id),
    supplier_id uuid references suppliers(id),
    status text not null default 'draft',
    total_amount decimal(10,2) default 0,
    remarks text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Create purchase_request_items table
create table if not exists purchase_request_items (
    id uuid default uuid_generate_v4() primary key,
    purchase_request_id uuid references purchase_requests(id) on delete cascade,
    item_description text not null,
    quantity decimal(10,2) not null,
    unit text not null,
    unit_price decimal(10,2) not null,
    total_price decimal(10,2) generated always as (quantity * unit_price) stored,
    account_code text,
    remarks text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Create trigger to update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger update_purchase_requests_updated_at
    before update on purchase_requests
    for each row
    execute function update_updated_at_column();

create trigger update_purchase_request_items_updated_at
    before update on purchase_request_items
    for each row
    execute function update_updated_at_column();

-- Create RLS policies
alter table purchase_requests enable row level security;
alter table purchase_request_items enable row level security;

create policy "Users can view their own purchase requests"
    on purchase_requests for select
    to authenticated
    using (requestor_id = auth.uid());

create policy "Users can insert their own purchase requests"
    on purchase_requests for insert
    to authenticated
    with check (requestor_id = auth.uid());

create policy "Users can update their own purchase requests"
    on purchase_requests for update
    to authenticated
    using (requestor_id = auth.uid());

create policy "Users can delete their own purchase requests"
    on purchase_requests for delete
    to authenticated
    using (requestor_id = auth.uid());

create policy "Users can view items in their purchase requests"
    on purchase_request_items for select
    to authenticated
    using (
        purchase_request_id in (
            select id from purchase_requests
            where requestor_id = auth.uid()
        )
    );

create policy "Users can insert items in their purchase requests"
    on purchase_request_items for insert
    to authenticated
    with check (
        purchase_request_id in (
            select id from purchase_requests
            where requestor_id = auth.uid()
        )
    );

create policy "Users can update items in their purchase requests"
    on purchase_request_items for update
    to authenticated
    using (
        purchase_request_id in (
            select id from purchase_requests
            where requestor_id = auth.uid()
        )
    );

create policy "Users can delete items in their purchase requests"
    on purchase_request_items for delete
    to authenticated
    using (
        purchase_request_id in (
            select id from purchase_requests
            where requestor_id = auth.uid()
        )
    );

-- Create indexes for better performance
create index if not exists idx_purchase_requests_requestor_id
    on purchase_requests(requestor_id);

create index if not exists idx_purchase_requests_supplier_id
    on purchase_requests(supplier_id);

create index if not exists idx_purchase_request_items_purchase_request_id
    on purchase_request_items(purchase_request_id);
