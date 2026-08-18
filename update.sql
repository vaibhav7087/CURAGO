UPDATE telephony_configurations SET credentials = credentials::jsonb || '{"amd_enabled": false, "record": false}'::jsonb WHERE provider = 'twilio';
