from os import getenv

# if env is prod read from env vars else read from local file

cred_dct = {}
ENV = getenv("ENV")
check_env = getenv("ORACLE_HOST")
if check_env:
    cred_dct["HOST"] = check_env
    cred_dct["USERNAME"] = getenv("ORACLE_USER")
    cred_dct["PASSWORD"] = getenv("ORACLE_PASS")
    cred_dct["SID"] = getenv("ORACLE_SID")
    cred_dct["PORT"] = getenv("ORACLE_PORT")
    print(f'connected to oracle db:  {cred_dct["HOST"]}')
else:
    cred_file = "/Users/spencer.trinhkinnate.com/Documents/security_files/oracle2"
    with open(cred_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            str_split = line.split(",")
            key = str_split[0].strip()
            value = str_split[1].strip()
            cred_dct[key] = value
    if ENV == "DEV":
        cred_dct["HOST"] = cred_dct["HOST-DEV"]
    print(f'connected to oracle db: {cred_dct["HOST"] }')
