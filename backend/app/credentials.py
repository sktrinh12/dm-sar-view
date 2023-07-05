from os import getenv

# if env is prod read from env vars else read from local file

cred_dct = {}
ENV = getenv("ENV")
DB_TYPE = getenv("DB_TYPE")
if ENV == "PROD":
    cred_dct["HOST"] = getenv("ORACLE_HOST")
    cred_dct["USERNAME"] = getenv("ORACLE_USER")
    cred_dct["PASSWORD"] = getenv("ORACLE_PASS")
    cred_dct["SID"] = getenv("ORACLE_SID")
    cred_dct["PORT"] = getenv("ORACLE_PORT")
    print(f'running in prod - {cred_dct["HOST"]}')
else:
    cred_file = "/Users/spencer.trinhkinnate.com/Documents/security_files/oracle2"
    with open(cred_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            str_split = line.split(",")
            key = str_split[0].strip()
            value = str_split[1].strip()
            cred_dct[key] = value
    print(
        f'running in dev: {cred_dct["HOST"] if ENV == "PROD" or DB_TYPE == "PROD" else cred_dct["HOST-DEV"]}'
    )
