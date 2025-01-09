# VIVITA Finance

A streamlined financial management system for VIVITA, built with Streamlit and Supabase.

## Features

- Dashboard with financial overview
- Purchase Request management
- Supplier management
- User authentication and authorization
- Settings configuration

## Prerequisites

- Python 3.8+
- Supabase account and project
- Environment variables configured

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vivita-finance.git
cd vivita-finance
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_API_SECRET=your_mailjet_api_secret
```

4. Run the application:
```bash
streamlit run src/main.py
```

## Project Structure

```
vivita-finance/
├── config/         # Configuration files
├── docs/          # Documentation
├── migrations/    # Database migrations
├── src/          # Source code
│   ├── crud/     # Database operations
│   ├── interfaces/ # UI interfaces
│   ├── utils/    # Utility functions
│   └── views/    # Streamlit views
├── tests/        # Test files
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential. All rights reserved.
