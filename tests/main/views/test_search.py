from lxml import html
import mock
import re
from ...helpers import BaseApplicationTest


def find_pagination_links(res_data):
    return re.findall(
        '<li class="[next|previous]+">[^<]+<a\ href="(/g-cloud/search\?[^"]+)',
        res_data,
        re.MULTILINE)


def find_search_summary(res_data):
    return re.findall(
        r'<span class="search-summary-count">.+</span>[^\n]+', res_data)


class TestSearchResults(BaseApplicationTest):
    def setup_method(self, method):
        super(TestSearchResults, self).setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self._search_api_client_presenters_patch = mock.patch('app.main.presenters.search_presenters.search_api_client',
                                                              autospec=True)
        self._search_api_client_presenters = self._search_api_client_presenters_patch.start()
        self._search_api_client_presenters.aggregate_services.return_value = \
            self._get_fixture_data('g9_aggregations_fixture.json')

        self.search_results = self._get_search_results_fixture_data()
        self.g9_search_results = self._get_g9_search_results_fixture_data()
        self.search_results_multiple_page = self._get_search_results_multiple_page_fixture_data()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        self._search_api_client_presenters_patch.stop()

    def test_search_page_results_service_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 200
        assert '<a href="/g-cloud/services/5-G3-0279-010">CDN VDMS</a>' in res.get_data(as_text=True)

    def test_search_page_form(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 200
        assert '<form action="/g-cloud/search" method="get">' in res.get_data(as_text=True)

    def test_search_page_allows_non_keyword_search(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        assert '<a href="/g-cloud/services/5-G3-0279-010">CDN VDMS</a>' in res.get_data(as_text=True)

    def test_should_not_render_pagination_on_single_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        assert '<li class="next">' not in res.get_data(as_text=True)
        assert '<li class="previous">' not in res.get_data(as_text=True)

    def test_should_render_pagination_link_on_first_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<li class="previous">' not in res.get_data(as_text=True)
        assert '<li class="next">' in res.get_data(as_text=True)

        (next_link,) = find_pagination_links(res.get_data(as_text=True))
        assert 'page=2' in next_link
        assert 'lot=cloud-software' in next_link

    def test_should_render_pagination_link_on_second_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software&page=2')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<li class="previous">' in res.get_data(as_text=True)
        assert '<li class="next">' in res.get_data(as_text=True)
        (prev_link, next_link) = find_pagination_links(
            res.get_data(as_text=True))

        assert 'page=1' in prev_link
        assert 'lot=cloud-software' in prev_link
        assert 'page=3' in next_link
        assert 'lot=cloud-software' in next_link

    def test_should_render_total_pages_on_pagination_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software&page=2')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<span class="page-numbers">1 of 200</span>' in res.get_data(as_text=True)
        assert '<span class="page-numbers">3 of 200</span>' in res.get_data(as_text=True)

    def test_should_render_pagination_link_on_last_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software&page=200')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<li class="previous">' in res.get_data(as_text=True)
        assert '<li class="next">' not in res.get_data(as_text=True)

        (prev_link,) = find_pagination_links(res.get_data(as_text=True))
        assert 'page=199' in prev_link
        assert 'lot=cloud-software' in prev_link

    def test_should_render_summary_for_0_results_in_all_categories_no_keywords(self):
        self._search_api_client.search_services.return_value = {
            "services": [],
            "meta": {
                "query": {},
                "total": 0,
                "took": 3
            },
            "links": {}
        }

        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">0</span> results found in <em>All categories</em>' in summary

    def test_should_render_summary_for_0_results_in_cloud_software_no_keywords(self):
        self._search_api_client.search_services.return_value = {
            "services": [],
            "meta": {
                "query": {},
                "total": 0,
                "took": 3
            },
            "links": {}
        }

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">0</span> results found in <em>Cloud software</em>' in summary

    def test_should_render_summary_for_1_result_in_cloud_software_no_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found in <em>Cloud software</em>' in summary

    def test_should_render_summary_for_1_result_in_cloud_hosting_no_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?lot=cloud-hosting')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' in <em>Cloud hosting</em>' in summary

    def test_should_render_summary_for_1_result_in_cloud_software_with_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?q=email&lot=cloud-software')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary

    def test_should_render_summary_with_a_group_of_1_boolean_filter(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' \
            ' where user support is available by <em>phone</em>' in summary

    def test_should_render_summary_with_a_group_of_2_boolean_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true&supportAvailableToThirdParty=true')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary
        assert ' where user support is available ' in summary
        assert 'that <em>can be used by third parties</em>' in summary
        assert 'by <em>phone</em>' in summary

    def test_should_render_summary_with_a_group_of_1_array_filter(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&resellingType=not_reseller')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' \
            ' where the supplier is <em>not a reseller</em>' \
            in summary

    def test_should_render_summary_with_a_group_of_2_array_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&resellingType=not_reseller&resellingType=reseller_no_extras')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' \
            ' where the supplier is ' in summary
        assert '<em>not a reseller</em>' in summary
        assert 'a <em>reseller (no extras)</em>' in summary

    def test_should_render_summary_with_2_groups_of_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true' +
            '&resellingType=not_reseller&resellingType=reseller_no_extras')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary
        assert ' where the supplier is ' in summary
        assert '<em>not a reseller</em>' in summary
        assert 'a <em>reseller (no extras)</em>' in summary
        assert ' where user support is available by <em>phone</em>' in summary

    def test_should_render_summary_with_3_groups_of_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true' +
            '&resellingType=not_reseller&resellingType=reseller_no_extras' +
            '&governmentSecurityClearances=dv')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary
        assert ' where the supplier is ' in summary
        assert '<em>not a reseller</em>' in summary
        assert 'a <em>reseller (no extras)</em>' in summary
        assert ' where user support is available by <em>phone</em>' in summary
        assert 'where suppliers are prepared to make sure their staff have <em>Developed Vetting (DV)</em>' in summary

    def test_should_ignore_unknown_arguments(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=&lot=cloud-software' +
            '&minimumContractPeriod=hr&minimumContractPeriod=dy')

        assert res.status_code == 200

    def test_query_text_is_escaped(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?q=<div>XSS</div>')

        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '&lt;div&gt;XSS&lt;/div&gt;' in summary

    def test_summary_for_unicode_query_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(u'/g-cloud/search?q=email+\U0001f47e&lot=cloud-software')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert u'<span class="search-summary-count">1</span> result found' \
            u' containing <em>email \U0001f47e</em> in' \
            u' <em>Cloud software</em>' in summary

    def test_should_404_on_invalid_page_param(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=1')
        assert res.status_code == 200

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=-1')
        assert res.status_code == 404

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=potato')
        assert res.status_code == 404

    def test_search_results_show_aggregations_by_lot(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        assert lots[0].text_content() == 'Cloud hosting (500)'
        assert lots[1].text_content() == 'Cloud software (500)'
        assert lots[2].text_content() == 'Cloud support (500)'

    def test_search_results_does_not_show_aggregation_for_lot_if_category_selected(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//li[@aria-current="page"]/strong')
        assert lots[0].text_content() == 'Cloud software'

    def test_search_results_show_aggregations_by_parent_category(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        category_matcher = re.compile('(.+) \((\d+)\)')
        expected_lot_counts = self._get_fixture_data('g9_aggregations_fixture.json')['aggregations']['service'
                                                                                                     'Categories']

        categories = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li')
        for category in categories:
            category_name, number_of_services = category_matcher.match(category.text_content()).groups()
            assert expected_lot_counts[category_name] == int(number_of_services)

    def test_search_results_does_not_show_aggregation_for_lot_or_parent_category_if_child_selected(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software&serviceCategories=accounting+and+finance')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        all_categories = document.xpath('//div[@class="lot-filters"]/ul/li')[0]
        assert all_categories.xpath('a[@class="lot-filters__top-level-link"]')[0].text_content() == 'All categories'

        cloud_software = all_categories.xpath('ul/li')[0]
        assert cloud_software.xpath('a[@class="lot-filters__top-level-link"]')[0].text_content() == 'Cloud software'

        parent_category = cloud_software.xpath('ul/li[@aria-current="page"]')[0]
        assert parent_category.xpath('strong')[0].text_content() == 'Accounting and finance'

    def test_search_results_show_aggregations_by_child_category(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software&serviceCategories=accounting+and+finance')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        category_matcher = re.compile('(.+) \((\d+)\)')
        expected_lot_counts = self._get_fixture_data('g9_aggregations_fixture.json')['aggregations']['service'
                                                                                                     'Categories']

        categories = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li')

        for category in categories:
            category_name, number_of_services = category_matcher.match(category.text_content()).groups()
            assert expected_lot_counts[category_name] == int(number_of_services)

    def test_lot_links_retain_all_category_filters(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?phoneSupport=true')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        for lot in lots:
            assert 'phoneSupport=true' in lot.get('href')

    def test_all_category_link_drops_lot_specific_filters(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&phoneSupport=true&scalingType=automatic')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]/ul/li/a')
        assert 'phoneSupport=true' in lots[0].get('href')
        assert 'scalingType=automatic' not in lots[0].get('href')

    def test_subcategory_link_retains_lot_specific_filters(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&phoneSupport=true&scalingType=automatic')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        category_links = document.xpath('//div[@class="lot-filters"]/ul/li/ul/li/ul/li/a')
        for category_link in category_links:
            assert 'phoneSupport=true' in category_link.get('href')
            assert 'scalingType=automatic' in category_link.get('href')

    def test_category_with_no_results_is_not_a_link(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-support')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        training = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//'
                                  'li[normalize-space(string())=$training]', training="Training (0)")
        assert len(training) == 1
        assert len(training[0].xpath('a')) == 0
