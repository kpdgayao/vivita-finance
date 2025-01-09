# VIVITA Finance

A finance management system for VIVITA built with Streamlit and Supabase.

## Features

- User Authentication (Login, Signup, Password Reset)
- Purchase Request Management
- Expense Reimbursement Forms (ERF)
- Voucher Management
- Supplier Management
- Role-based Access Control (Finance, Admin, User)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vivita-finance.git
cd vivita-finance
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up Supabase:
   - Create a new project at [Supabase](https://supabase.com)
   - Run the SQL scripts in the `sql/` directory to set up tables and triggers
   - Copy `config/config.example.yaml` to `config/config.yaml` and update with your credentials:
     ```bash
     cp config/config.example.yaml config/config.yaml
     ```

4. Run the application:
```bash
streamlit run src/main.py
```

## Database Schema

### Profiles Table
```sql
create table public.profiles (
    id uuid not null,
    first_name text not null,
    last_name text not null,
    email text not null,
    role text not null,
    created_at timestamp with time zone not null default timezone ('utc'::text, now()),
    updated_at timestamp with time zone not null default timezone ('utc'::text, now()),
    constraint profiles_pkey primary key (id),
    constraint profiles_email_key unique (email),
    constraint profiles_id_fkey foreign key (id) references auth.users (id),
    constraint profiles_role_check check (role = any (array['Finance'::text, 'Admin'::text, 'User'::text]))
);
```

## Project Structure

```
vivita-finance/
├── config/
│   ├── config.example.yaml    # Example configuration file
│   └── config.yaml           # Local configuration (not in git)
├── sql/
│   ├── create_profiles_table.sql
│   └── add_user_trigger.sql
├── src/
│   ├── interfaces/          # Interface components
│   ├── managers/           # Business logic
│   ├── models/            # Data models
│   ├── views/            # UI components
│   ├── config.py        # Configuration loader
│   └── main.py         # Main application
├── .gitignore
├── README.md
├── requirements.txt
└── setup.py
```

## Development

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "Description of your changes"
```

3. Push your changes:
```bash
git push origin feature/your-feature-name
```

## Security

- Never commit sensitive information (API keys, passwords, etc.)
- Always use environment variables or config files for secrets
- Keep the config.yaml file in .gitignore

## License

[Your License Here]
