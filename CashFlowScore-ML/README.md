## Pavan integration

- `/score` accepts either a full feature dict or `business_id`.
- If you pass `business_id`, the service fetches the feature payload from Pavan's `/features/{business_id}` endpoint.
- Set `PAVAN_FEATURES_URL` to the base URL of Pavan's service, for example `http://127.0.0.1:8001`.
- The response includes `source` so you can see whether the score came from direct features or Pavan.

