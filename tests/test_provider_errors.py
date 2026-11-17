import io
import json
import unittest
import urllib.error
from rwstudio.provider import provider_error

class ProviderErrorTests(unittest.TestCase):
 def error(self,code,kind='',headers=None):
  return urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'error',headers or {},io.BytesIO(json.dumps({'error':{'code':code,'type':kind,'message':'private-key-and-prompt'}}).encode()))
 def test_credit_exhaustion_is_distinct_from_rate_limiting(self):
  message=provider_error(self.error('credit_balance_exhausted','insufficient_quota'),'openai')
  self.assertIn('credits are exhausted',message);self.assertNotIn('private-key',message);self.assertNotIn('Wait',message)
 def test_rate_limit_uses_retry_after_without_billing_claim(self):
  message=provider_error(self.error('rate_limit_exceeded','rate_limit_error',{'Retry-After':'12'}),'openai')
  self.assertIn('12 seconds',message);self.assertNotIn('billing',message.lower())
 def test_spending_limit_and_generic_quota_classified(self):
  self.assertIn('project reached its spending limit',provider_error(self.error('project_spend_limit_exceeded'),'openai'))
  self.assertIn('insufficient API quota',provider_error(self.error(None,'insufficient_quota'),'openai'))
 def test_malformed_response_never_exposes_raw_content(self):
  for raw in (b'not-json-secret',b'[]',b'{"error":"private-secret"}'):
   exc=urllib.error.HTTPError('https://example.com',429,'error',{},io.BytesIO(raw))
   message=provider_error(exc,'openai');self.assertIn('HTTP 429',message);self.assertNotIn('secret',message)
