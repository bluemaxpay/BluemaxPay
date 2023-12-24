-- disable bluemax payment provider
UPDATE payment_provider
   SET secret_api_key = NULL,
       public_api_key = NULL,
       license_id = NULL,
       device_id = NULL,
       username = NULL,
       password = NULL,
       developer_id = NULL,
       version_number = NULL;