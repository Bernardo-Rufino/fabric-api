"""
Unit tests for the Auth class — scope selection and validation.

These tests mock Azure credentials and do not perform real authentication.

Usage:
    pytest tests/test_auth.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fabric_api.auth import Auth


# ===========================================================================
# get_token — scope selection
# ===========================================================================

class TestGetToken:

    @patch('fabric_api.auth.ClientSecretCredential')
    def test_pbi_scope(self, mock_cred_cls):
        mock_cred = MagicMock()
        mock_cred.get_token.return_value = MagicMock(token='fake-pbi-token')
        mock_cred_cls.return_value = mock_cred

        auth = Auth('tenant', 'client', 'secret')
        token = auth.get_token('pbi')

        assert token == 'fake-pbi-token'
        mock_cred.get_token.assert_called_once_with(
            'https://analysis.windows.net/powerbi/api/.default'
        )

    @patch('fabric_api.auth.ClientSecretCredential')
    def test_fabric_scope(self, mock_cred_cls):
        mock_cred = MagicMock()
        mock_cred.get_token.return_value = MagicMock(token='fake-fabric-token')
        mock_cred_cls.return_value = mock_cred

        auth = Auth('tenant', 'client', 'secret')
        token = auth.get_token('fabric')

        assert token == 'fake-fabric-token'
        mock_cred.get_token.assert_called_once_with(
            'https://api.fabric.microsoft.com/.default'
        )

    def test_invalid_service_raises(self):
        auth = Auth('tenant', 'client', 'secret')
        with pytest.raises(ValueError, match="Invalid service"):
            auth.get_token('invalid')


# ===========================================================================
# get_token_for_user — scope selection
# ===========================================================================

class TestGetTokenForUser:

    def test_invalid_service_raises(self):
        auth = Auth('tenant', 'client', 'secret')
        with pytest.raises(ValueError, match="Invalid service"):
            auth.get_token_for_user('invalid')

    @patch('fabric_api.auth.InteractiveBrowserCredential')
    def test_azure_scope(self, mock_cred_cls):
        mock_cred = MagicMock()
        mock_cred.get_token.return_value = MagicMock(token='fake-azure-token')
        mock_cred_cls.return_value = mock_cred

        auth = Auth('tenant', 'client', 'secret')
        token = auth.get_token_for_user('azure')

        assert token == 'fake-azure-token'
        mock_cred.get_token.assert_called_once_with(
            'https://management.azure.com/.default'
        )
