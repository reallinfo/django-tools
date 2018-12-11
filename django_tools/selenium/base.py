"""
    :created: 2015 by Jens Diemer
    :copyleft: 2015-2018 by the django-tools team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""
import logging
import sys
import traceback
import unittest

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

# https://github.com/jedie/django-tools
from django_tools.selenium.response import selenium2fakes_response

log = logging.getLogger(__name__)


class SeleniumBaseTestCase(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if cls.driver is not None:
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        if self.driver is not None:
            self.driver.delete_all_cookies()

    def _wait(self, conditions, timeout=5, msg="wait timeout"):
        """
        Wait for the given condition.
        Display page_source on error.
        """
        try:
            check = WebDriverWait(self.driver, timeout).until(conditions)
        except TimeoutException as err:
            print("\nError: %s\n%s\npage source:\n%s\n" % (msg, err, self.driver.page_source))
            raise
        else:
            self.assertTrue(check)

    def get_faked_response(self):
        """
        Create a similar 'testing-response' [1] here.
        So that some of the django testing assertions [2] can be used
        with selenium tests, too ;)

        Currently not available:
            * response.status_code
            * response.redirect_chain
            * response.templates
            * response.context

        Available:
            * response.content
            * response.cookies
            * response.client.cookies
            * response.session

        [1] https://docs.djangoproject.com/en/1.11/topics/testing/tools/#testing-responses
        [2] https://docs.djangoproject.com/en/1.11/topics/testing/tools/#assertions
        """
        return selenium2fakes_response(self.driver, self.client, self.client_class)

    def _verbose_assertion_error(self, err):
        sys.stderr.write("\n\n")
        sys.stderr.flush()
        sys.stderr.write("*" * 79)
        sys.stderr.write("\n")

        traceback.print_exc()

        sys.stderr.write(" -" * 40)
        sys.stderr.write("\n")
        try:
            page_source = self.driver.page_source
        except Exception as e:
            print("Can't get 'driver.page_source': %s" % e)
        else:
            page_source = "\n".join([line for line in page_source.splitlines() if line.rstrip()])
            print(page_source, file=sys.stderr)

        sys.stderr.write("*" * 79)
        sys.stderr.write("\n")
        sys.stderr.write("\n\n")
        sys.stderr.flush()

        raise AssertionError(err)

    def assert_no_javascript_alert(self):
        alert = expected_conditions.alert_is_present()(self.driver)
        if alert != False:
            alert_text = alert.text
            alert.accept()  # Confirm a alert dialog, otherwise access to driver.page_source will failed!
            try:
                raise self.failureException("Alert is preset: %s" % alert_text)
            except AssertionError as err:
                self._verbose_assertion_error(err)

    def assert_equal_page_title(self, should):
        try:
            self.assertEqual(self.driver.title, should)
        except AssertionError as err:
            self._verbose_assertion_error(err)

    def assert_in_page_source(self, member):
        try:
            self.assertIn(member, self.driver.page_source)
        except AssertionError as err:
            self._verbose_assertion_error(err)

    def assert_not_in_page_source(self, member):
        try:
            self.assertNotIn(member, self.driver.page_source)
        except AssertionError as err:
            self._verbose_assertion_error(err)

    def assert_visible_by_id(self, id, timeout=10):
        """
        Test that an element by ID is present on the DOM of a page and visible.
        """
        locator = (By.ID, id)
        self._wait(
            conditions=expected_conditions.visibility_of_element_located(locator),
            timeout=timeout,
            msg="Wait for '#%s' to be visible. (timeout: %i)" % (id, timeout),
        )

    def assert_clickable_by_id(self, id, timeout=10):
        """
        Test that an element by ID is visible and enabled such that you can click it
        """
        locator = (By.ID, id)
        self._wait(
            conditions=expected_conditions.element_to_be_clickable(locator),
            timeout=timeout,
            msg="Wait for '#%s' to be clickable. (timeout: %i)" % (id, timeout),
        )

    def assert_clickable_by_xpath(self, xpath, timeout=10):
        """
        Test that an element by ID is visible and enabled such that you can click it
        """
        locator = (By.XPATH, xpath)
        self._wait(
            conditions=expected_conditions.element_to_be_clickable(locator),
            timeout=timeout,
            msg="Wait for '%s' to be clickable. (timeout: %i)" % (xpath, timeout),
        )