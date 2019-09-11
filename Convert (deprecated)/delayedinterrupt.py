# This file provides a class that allows the delaying of keyboard interrupts for blocks of code
# that should not be interrupted. This is used in `convert_script.py` to ensure that we get a clean
# break when we're processing videos -- sometimes this means a long wait time, but that's okay.
#
# This class is adapted from the following stackoverflow answer:
# https://stackoverflow.com/a/21919644

import signal

class DelayedInterrupt():
	def __enter__(self):
		self.enable()

		return self

	def enable(self):
		if hasattr(self, 'is_enabled') and self.is_enabled:
			return

		self.signal_received = False
		# signal.signal returns the previous handler
		self.old_handler = signal.signal(signal.SIGINT, self.handler)

		self.is_enabled = True

	def handler(self, sig, frame):
		self.signal_received = (sig, frame)
		print('SIGINT received. Delaying until finished.')

	def disable(self):
		if not self.is_enabled:
			return

		signal.signal(signal.SIGINT, self.old_handler)
		if self.signal_received:
			self.old_handler(*self.signal_received)

		self.is_enabled = False

	def __exit__(self, type, value, traceback):
		self.disable()
