import datetime
import logging
from logging.handlers import BufferingHandler
import os
from types import MethodType
from res.enkf import ErtScript
from semeio.communication.reporter import FileReporter


class _LogHandlerContext(object):
    def __init__(self, log, handler):
        self._log = log
        self._handler = handler

    def __enter__(self):
        self._log.addHandler(self._handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._log.removeHandler(self._handler)


class _ReportHandler(BufferingHandler):
    def __init__(self, output_dir):
        super(_ReportHandler, self).__init__(1)
        self._reporter = FileReporter(output_dir)
        self._namespace = "log.txt"

    def flush(self):
        for log_record in self.buffer:
            self._reporter.publish_msg(self._namespace, self._format_record(log_record))

        super(_ReportHandler, self).flush()

    def _format_record(self, log_record):
        log_fmt = "{log_level} [{log_time}]: {log_message}"
        return log_fmt.format(
            log_level=log_record.levelname,
            log_time=datetime.datetime.fromtimestamp(log_record.created),
            log_message=log_record.message,
        )


class SemeioScript(ErtScript):  # pylint: disable=too-few-public-methods
    """
    SemeioScript is a workflow utility extending the functionality of ErtScript.
    In particular it provides a `self.reporter` instance available for passing
    data to the common storage. In addition, while `self.run` is being executed
    it forwards log statements to the reporter as well.
    """

    def __init__(self, ert):
        super(SemeioScript, self).__init__(ert)
        self._output_dir = self._get_output_dir()
        self._reporter = FileReporter(self._output_dir)
        self._wrap_run()

    def _wrap_run(self):
        # pylint: disable=access-member-before-definition
        self._real_run = self.run

        def run_with_handler(self, *args):
            log = logging.getLogger("")
            report_handler = _ReportHandler(self._output_dir)
            with _LogHandlerContext(log, report_handler):
                self._real_run(args)

        self.run = MethodType(run_with_handler, self)

    def _get_output_dir(self):
        base_dir = self.ert().resConfig().model_config.getEnspath()
        base_dir = os.path.realpath(base_dir)
        return os.path.join(base_dir, "reports", type(self).__name__,)

    @property
    def reporter(self):
        return self._reporter
