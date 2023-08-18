## SAR-VEW

#### Summary

This external app displays compound ids and their properties with highlighted rows based on a date range.

#### Technical

Specifically, it ingests query parameters, `-TABLENAME-` passed from DM UI to
pre-populate a textarea with compound ids that are to be viewed for structure activity relationship analysis. The `-TABLENAME-` mask will direct the backend to select the `COMPOUND_ID` column from the corresponding query table.
This is only the frontend UI. The geomean fastapi python backend `https://github.com/Kinnate/geomean-ic50-flagger.git` is used to generate the SQL and run it against the connected Oracle database. The application was deployed using
Jenkins CI/CD pipline. The `Jenkinsfile` can be inspected to understand what is performed. Basically, the docker image is built, then pushed to ECR, then deployed using `helm`. The app lives in the main `apps` namespace within `helm`
as well as `kubectl`. Run `kubectl get all -n apps -l app=sar-view` to get the kubernetes resources. Currently, the app can be visited by navigating to: `http://sar-view.kinnate`.

#### Additional notes

Once jenkins deploys the app and the pods and services are running the next step
is to expose the application through a kubernetes nginx ingress. Just as in any other app, one must add a new ingress rule to the
ingress yaml file. This can be obtained by running: `kubectl get ingress -o yaml` and applyling it locally, or editing the yaml on the fly (expert user)
like so: `kubectl edit ingress -n apps`. The ingress rule block should resemble
something like:

```
    - host: $APP_NAME.kinnate
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: $APP_NAME-svc
                port:
                  name: http
```

Then ensure this A-record is added to Route 53 with the appropriate LoadBalancer
name as the `Route traffic to` value.

### Update sql datasource

The biochemical geomean SQL statement is extracted from http://sql-ds.kinnate
service and formatted properly for the SAR view. If changes were made to the SQL
source on the Dotmatics side, use this endpoint to update the SQL:
`http://sar-view-backend.kinnate/v1/update_sql_ds`. Restarting the pods will alsoachieve the same result since it will retrieve the SQL on start-up. **Test the sql-datasource service after making changes to the SQL on the DM side**
An example payload would be:
`{"biochemical": {"id": 912,"app_type": "geomean_sar"}}`
