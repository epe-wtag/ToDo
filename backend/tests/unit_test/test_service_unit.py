import unittest
from unittest.mock import patch, MagicMock


from app import core


class TestEmailFunctions(unittest.TestCase):
    @patch("app.core.templates.Jinja2Templates.get_template")
    @patch("app.core.fastapi_mail.FastMail.send_message")
    async def test_simple_send_success(self, mock_send_message, mock_get_template):
        email = "test@example.com"
        token = "test_token"
        expected_html = "<html><body>Test HTML</body></html>"
        mock_get_template.return_value.render.return_value = expected_html
        mock_send_message.return_value = MagicMock()

        response = await core.simple_send(email, token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, {"message": "Email has been sent"})
        mock_get_template.assert_called_once_with(
            "verification_email.html",
            {
                "verify_url": "http://127.0.0.1:8000/api/v1/auth/verify",
                "email": email,
                "token": token,
            },
        )
        mock_send_message.assert_called_once()

    @patch("app.core.security.generate_verification_token")
    @patch("app.core.simple_send")
    async def test_send_verification_email_success(
        self, mock_simple_send, mock_generate_verification_token
    ):
        email = "test@example.com"
        token = "test_token"
        mock_generate_verification_token.return_value = token
        mock_simple_send.return_value = MagicMock()

        await core.send_verification_email(email)

        mock_generate_verification_token.assert_called_once_with(email)
        mock_simple_send.assert_called_once_with(email, token)

    @patch("app.core.templates.Jinja2Templates.get_template")
    @patch("app.core.fastapi_mail.FastMail.send_message")
    async def test_send_reset_email_success(self, mock_send_message, mock_get_template):
        email = "test@example.com"
        token = "test_token"
        expected_html = "<html><body>Test HTML</body></html>"
        mock_get_template.return_value.render.return_value = expected_html
        mock_send_message.return_value = MagicMock()

        response = await core.send_reset_email(email, token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, {"message": "Email has been sent"})
        mock_get_template.assert_called_once_with(
            "reset_password_email.html", {"email": email, "token": token}
        )
        mock_send_message.assert_called_once()
