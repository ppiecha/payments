# App
APP_TITLE = 'Web service of a basic payment system'

# Env variables
DATABASE_URL = 'postgresql://postgres:db_password@localhost:5432/payments'

# Endpoint
CREATE_USER = '/create_user/'
DEPOSIT_MONEY = '/deposit_money/'
TRANSFER_MONEY = '/transfer_money/'

# Test URL
TEST_URL = 'http://127.0.0.1:8003'

# Other constants
YES = 'Y'
NO = 'N'

# Tables
USERS = """
    CREATE TABLE IF NOT EXISTS public.users
    (
        id serial PRIMARY KEY,
        first_name varchar(64) NOT NULL,
        last_name varchar(64) NOT NULL
    )
"""

WALLETS = """
    CREATE TABLE IF NOT EXISTS public.wallets
    (
        id serial PRIMARY KEY,
        user_id bigint NOT NULL,
        balance numeric NOT NULL DEFAULT 0,
        CONSTRAINT user_uk UNIQUE (user_id),
        CONSTRAINT user_fk FOREIGN KEY (user_id)
            REFERENCES public.users (id) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION
    )
"""

TRANSACTIONS = """
    CREATE TABLE IF NOT EXISTS public.transactions
    (
        id serial PRIMARY KEY,
        wallet_id bigint NOT NULL,
        type varchar(32) NOT NULL,
        amount numeric NOT NULL,
        transaction_timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT wallet_fk FOREIGN KEY (wallet_id)
            REFERENCES public.wallets (id) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION,
        CONSTRAINT type_ck CHECK (type in ('credit', 'debit'))
    )
"""
