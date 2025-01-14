-- Create audit trail table for purchase requests
create table if not exists public.purchase_request_audit (
    id uuid primary key default uuid_generate_v4(),
    purchase_request_id uuid not null references public.purchase_requests(id) on delete cascade,
    user_id uuid not null references auth.users(id),
    action varchar(255) not null,
    details text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    constraint purchase_request_audit_action_check 
        check (action in ('created', 'updated', 'deleted', 'status_changed', 'comment_added'))
);

-- Add indexes for better query performance
create index if not exists idx_pr_audit_pr_id on public.purchase_request_audit(purchase_request_id);
create index if not exists idx_pr_audit_user_id on public.purchase_request_audit(user_id);
create index if not exists idx_pr_audit_created_at on public.purchase_request_audit(created_at);

-- Add RLS policies
alter table public.purchase_request_audit enable row level security;

-- Allow authenticated users to view audit entries
create policy "Users can view audit entries"
    on public.purchase_request_audit for select
    to authenticated
    using (true);

-- Only the system can insert audit entries
create policy "System can insert audit entries"
    on public.purchase_request_audit for insert
    to authenticated
    using (true);

-- Function to automatically add audit entry when PR status changes
create or replace function public.handle_purchase_request_status_change()
returns trigger as $$
begin
    if OLD.status <> NEW.status then
        insert into public.purchase_request_audit (
            purchase_request_id,
            user_id,
            action,
            details
        ) values (
            NEW.id,
            auth.uid(),
            'status_changed',
            format('Status changed from %s to %s', OLD.status, NEW.status)
        );
    end if;
    return NEW;
end;
$$ language plpgsql security definer;

-- Trigger for status changes
create trigger on_purchase_request_status_change
    after update of status on public.purchase_requests
    for each row
    execute function public.handle_purchase_request_status_change();
