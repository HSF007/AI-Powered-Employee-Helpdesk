## Set-up and Installation

* Installing requirements in python (check if you are in backend folder):
```bash
python -m pip install -r requirements.txt
```

* Creating Schema in database (check if you are in main project folder)
```bash
psql -U postgres -d helpdesk -f database/schema.sql
```

**If the above command doesn't work try the following**
```bash
& "C:\Program Files\PostgreSQL\<VERSION>\bin\psql.exe" -U psql -U postgres -d helpdesk -f database/schema.sql
```

**Like following command**
```bash
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U psql -U postgres -d helpdesk -f database/schema.sql
```

* To add sample data in database run
```bash
psql -U postgres -d helpdesk -f database/seed.sql
```

* To run quries you can run:
```bash
psql -U postgres -d helpdesk -f database/queries.sql
```

* To save query in text file run:
```bash
psql -U postgres -d helpdesk -f database/queries.sql -o docs/query-results.txt
```
