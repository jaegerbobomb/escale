# Run the Nextcloud tests

The Nextcloud adapter (`escale_core.adapters.nextcloud_dav`) is tested against a real
server. CI starts one in a container (job `nextcloud`); to run the same tests on your
machine, with Docker:

```bash
docker run -d --name escale-nextcloud -p 8080:80 \
  -e SQLITE_DATABASE=nextcloud \
  -e NEXTCLOUD_ADMIN_USER=admin -e NEXTCLOUD_ADMIN_PASSWORD=escale-test-pw \
  -e NEXTCLOUD_TRUSTED_DOMAINS="localhost 127.0.0.1" \
  nextcloud:31-apache
# wait until http://127.0.0.1:8080/status.php says "installed":true, then:
export ESCALE_NEXTCLOUD_URL=http://127.0.0.1:8080 ESCALE_NEXTCLOUD_LOGIN=admin
export ESCALE_NEXTCLOUD_PASSWORD=$(curl -fs -u admin:escale-test-pw \
  -H 'OCS-APIRequest: true' \
  'http://127.0.0.1:8080/ocs/v2.php/core/getapppassword?format=json' \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["ocs"]["data"]["apppassword"])')
uv run pytest packages/escale-core/tests/test_nextcloud_dav.py
```

Without these variables the tests are skipped. They create and delete a "Trips"
calendar and an "Escale" folder: never point them at a Nextcloud you use.
