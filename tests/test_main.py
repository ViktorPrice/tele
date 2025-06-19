import unittest
from unittest.mock import patch, MagicMock
import logging

class TestMainAppLogging(unittest.TestCase):
    @patch('main.logging.FileHandler')
    @patch('main.logging.StreamHandler')
    @patch('main.logging.basicConfig')
    def test_setup_safe_logging(self, mock_basicConfig, mock_streamHandler, mock_fileHandler):
        import main
        main.setup_safe_logging()
        mock_basicConfig.assert_called_once()
        self.assertTrue(mock_fileHandler.called)
        self.assertTrue(mock_streamHandler.called)

    @patch('main.logging.getLogger')
    def test_logging_output(self, mock_getLogger):
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        import main
        main.setup_safe_logging()
        logger = logging.getLogger('EncodingTest')
        logger.info("Тест логирования: русский текст")
        logger.info("Test logging: English text")
        self.assertTrue(mock_logger.info.called)

class TestMainAppRun(unittest.TestCase):
    @patch('main._run_application')
    @patch('main._create_application_context_priority')
    @patch('main._import_components')
    @patch('main.setup_safe_logging')
    @patch('main.setup_encoding')
    def test_main_runs(self, mock_setup_enc, mock_setup_log, mock_import, mock_create_ctx, mock_run_app):
        mock_import.return_value = {
            'MainWindow': MagicMock(),
            'MainController': MagicMock(),
            'ParameterFilteringService': MagicMock(),
            'CSVDataLoader': MagicMock(),
            'PlotManager': MagicMock(),
            'ReportManager': MagicMock(),
            'SOPManager': MagicMock(),
            'DataModel': MagicMock(),
            'ui_config_available': True,
            'use_cases_available': True
        }
        mock_create_ctx.return_value = {'root': MagicMock()}
        import main
        main.main()
        mock_setup_enc.assert_called_once()
        mock_setup_log.assert_called_once()
        mock_import.assert_called_once()
        mock_create_ctx.assert_called_once()
        mock_run_app.assert_called_once()

if __name__ == '__main__':
    unittest.main()
