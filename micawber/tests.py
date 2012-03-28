import unittest
try:
    import simplejson as json
except ImportError:
    import json

from micawber import *
from micawber.providers import make_key


class TestProvider(Provider):
    test_data = {
        # link
        'link?format=json&url=http%3A%2F%2Flink-test1': {'title': 'test1', 'type': 'link'},
        'link?format=json&url=http%3A%2F%2Flink-test2': {'title': 'test2', 'type': 'link'},

        # photo
        'photo?format=json&url=http%3A%2F%2Fphoto-test1': {'title': 'ptest1', 'url': 'test1.jpg', 'type': 'photo'},
        'photo?format=json&url=http%3A%2F%2Fphoto-test2': {'title': 'ptest2', 'url': 'test2.jpg', 'type': 'photo'},
        
        # video
        'video?format=json&url=http%3A%2F%2Fvideo-test1': {'title': 'vtest1', 'html': '<test1>video</test1>', 'type': 'video'},
        'video?format=json&url=http%3A%2F%2Fvideo-test2': {'title': 'vtest2', 'html': '<test2>video</test2>', 'type': 'video'},

        # rich
        'rich?format=json&url=http%3A%2F%2Frich-test1': {'title': 'rtest1', 'html': '<test1>rich</test1>', 'type': 'rich'},
        'rich?format=json&url=http%3A%2F%2Frich-test2': {'title': 'rtest2', 'html': '<test2>rich</test2>', 'type': 'rich'},

        # with param
        'link?format=json&url=http%3A%2F%2Flink-test1&width=100': {'title': 'test1', 'type': 'link', 'width': 99},
    }

    def fetch(self, url):
        if url in self.test_data:
            return json.dumps(self.test_data[url])
        return False

test_pr = ProviderRegistry()

test_cache = Cache()
test_pr_cache = ProviderRegistry(test_cache)

for pr in (test_pr, test_pr_cache):
    pr.register('http://link\S*', TestProvider('link'))
    pr.register('http://photo\S*', TestProvider('photo'))
    pr.register('http://video\S*', TestProvider('video'))
    pr.register('http://rich\S*', TestProvider('rich'))

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        test_cache._cache = {}

        self.full_pairs = {
            'http://link-test1': '<a href="http://link-test1" title="test1">test1</a>',
            'http://photo-test2': '<a href="test2.jpg" title="ptest2"><img alt="ptest2" src="test2.jpg" /></a>',
            'http://video-test1': '<test1>video</test1>',
            'http://rich-test2': '<test2>rich</test2>',
        }

        self.inline_pairs = {
            'http://link-test1': '<a href="http://link-test1" title="test1">test1</a>',
            'http://photo-test2': '<a href="test2.jpg" title="ptest2">ptest2</a>',
            'http://video-test1': '<a href="http://video-test1" title="vtest1">vtest1</a>',
            'http://rich-test2': '<a href="http://rich-test2" title="rtest2">rtest2</a>',
        }

        self.data_pairs = {
            'http://link-test1': {'title': 'test1', 'type': 'link'},
            'http://photo-test2': {'title': 'ptest2', 'url': 'test2.jpg', 'type': 'photo'},
            'http://video-test1': {'title': 'vtest1', 'html': '<test1>video</test1>', 'type': 'video'},
            'http://rich-test2': {'title': 'rtest2', 'html': '<test2>rich</test2>', 'type': 'rich'},
        }

    def assertCached(self, url, data, **params):
        key = make_key(url, params)
        self.assertTrue(key in test_cache._cache)
        self.assertEqual(test_cache._cache[key], data)

class ProviderTestCase(BaseTestCase):
    def test_provider_matching(self):
        provider = test_pr.provider_for_url('http://link-test1')
        self.assertFalse(provider is None)
        self.assertEqual(provider.endpoint, 'link')

        provider = test_pr.provider_for_url('http://photo-test1')
        self.assertFalse(provider is None)
        self.assertEqual(provider.endpoint, 'photo')

        provider = test_pr.provider_for_url('http://video-test1')
        self.assertFalse(provider is None)
        self.assertEqual(provider.endpoint, 'video')

        provider = test_pr.provider_for_url('http://rich-test1')
        self.assertFalse(provider is None)
        self.assertEqual(provider.endpoint, 'rich')

        provider = test_pr.provider_for_url('http://none-test1')
        self.assertTrue(provider is None)

    def test_provider(self):
        resp = test_pr.request('http://link-test1')
        self.assertEqual(resp, {'title': 'test1', 'type': 'link', 'url': 'http://link-test1'})

        resp = test_pr.request('http://photo-test2')
        self.assertEqual(resp, {'title': 'ptest2', 'type': 'photo', 'url': 'test2.jpg'})

        resp = test_pr.request('http://video-test1')
        self.assertEqual(resp, {'title': 'vtest1', 'type': 'video', 'html': '<test1>video</test1>', 'url': 'http://video-test1'})

        resp = test_pr.request('http://link-test1', width=100)
        self.assertEqual(resp, {'title': 'test1', 'type': 'link', 'url': 'http://link-test1', 'width': 99})

        self.assertRaises(ProviderException, test_pr.request, 'http://not-here')
        self.assertRaises(ProviderException, test_pr.request, 'http://link-test3')
    
    def test_caching(self):
        resp = test_pr_cache.request('http://link-test1')
        self.assertCached('http://link-test1', resp)

        # check that its the same as what we tested in the previous case
        resp2 = test_pr.request('http://link-test1')
        self.assertEqual(resp, resp2)

        resp = test_pr_cache.request('http://photo-test2')
        self.assertCached('http://photo-test2', resp)

        resp = test_pr_cache.request('http://video-test1')
        self.assertCached('http://video-test1', resp)

        self.assertEqual(len(test_cache._cache), 3)

    def test_caching_params(self):
        resp = test_pr_cache.request('http://link-test1')
        self.assertCached('http://link-test1', resp)

        resp_p = test_pr_cache.request('http://link-test1', width=100)
        self.assertCached('http://link-test1', resp_p, width=100)

        self.assertFalse(resp == resp_p)


class ParserTestCase(BaseTestCase):
    def test_parse_text_full(self):
        for url, expected in self.full_pairs.items():
            parsed = parse_text_full(url, test_pr)
            self.assertEqual(parsed, expected)
        
        # the parse_text_full will replace even inline content
        for url, expected in self.full_pairs.items():
            parsed = parse_text_full('this is inline: %s' % url, test_pr)
            self.assertEqual(parsed, 'this is inline: %s' % expected)

        for url, expected in self.full_pairs.items():
            parsed = parse_html('<p>%s</p>' % url, test_pr)
            self.assertEqual(parsed, '<p>%s</p>' % expected)

    def test_parse_text(self):
        for url, expected in self.inline_pairs.items():
            parsed = parse_text('this is inline: %s' % url, test_pr)
            self.assertEqual(parsed, 'this is inline: %s' % expected)

        # if the link comes on its own line it gets included in full
        for url, expected in self.full_pairs.items():
            parsed = parse_text(url, test_pr)
            self.assertEqual(parsed, expected)

        # links inside block tags will render as inline
        frame = '<p>Testing %s</p>'
        for url, expected in self.inline_pairs.items():
            parsed = parse_html(frame % (url), test_pr)
            self.assertEqual(parsed, frame % (expected))

        # links inside <a> tags won't change at all
        frame = '<p><a href="%s">%s</a></p>'
        for url, expected in self.inline_pairs.items():
            parsed = parse_html(frame % (url, url), test_pr)
            self.assertEqual(parsed, frame % (url, url))

        # links within tags within a tags are fine too
        frame = '<p><a href="%s"><span>%s</span></a></p>'
        for url, expected in self.inline_pairs.items():
            parsed = parse_html(frame % (url, url), test_pr)
            self.assertEqual(parsed, frame % (url, url))

    def test_multiline(self):
        for url, expected in self.full_pairs.items():
            expected_inline = self.inline_pairs[url]
            frame = 'this is inline: %s\n%s\nand yet another %s'

            test_str = frame % (url, url, url)

            parsed = parse_text(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected_inline, expected, expected_inline))

        for url, expected in self.full_pairs.items():
            expected_inline = self.inline_pairs[url]
            frame = '%s\nthis is inline: %s\n%s'

            test_str = frame % (url, url, url)

            parsed = parse_text(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected, expected_inline, expected))

        # test mixing multiline with p tags
        for url, expected in self.full_pairs.items():
            expected_inline = self.inline_pairs[url]
            frame = '<p>%s</p>\n<p>this is inline: %s</p>\n<p>\n%s\n</p><p>last test\n%s\n</p>'

            test_str = frame % (url, url, url, url)

            parsed = parse_html(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected, expected_inline, expected, expected_inline))

        for url, expected in self.full_pairs.items():
            expected_inline = self.inline_pairs[url]
            frame = '<p><a href="#foo">%s</a></p>\n<p>this is inline: %s</p>\n<p>last test\n%s\n</p>'

            test_str = frame % (url, url, url)

            parsed = parse_html(test_str, test_pr)
            self.assertEqual(parsed, frame % (url, expected_inline, expected_inline))

    def test_multiline_full(self):
        for url, expected in self.full_pairs.items():
            frame = 'this is inline: %s\n%s\nand yet another %s'

            test_str = frame % (url, url, url)

            parsed = parse_text_full(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected, expected, expected))

    def test_urlize(self):
        blank = 'http://fapp.io/foo/'
        blank_e = '<a href="http://fapp.io/foo/">http://fapp.io/foo/</a>'
        for url, expected in self.full_pairs.items():
            expected_inline = self.inline_pairs[url]
            frame = 'test %s\n%s\n%s\nand finally %s'

            test_str = frame % (url, blank, url, blank)

            parsed = parse_text(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected_inline, blank_e, expected, blank_e))

            parsed = parse_text(test_str, test_pr, urlize_all=False)
            self.assertEqual(parsed, frame % (expected_inline, blank, expected, blank))

            parsed = parse_text_full(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected, blank_e, expected, blank_e))

            parsed = parse_text_full(test_str, test_pr, urlize_all=False)
            self.assertEqual(parsed, frame % (expected, blank, expected, blank))

            parsed = parse_html(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected_inline, blank_e, expected_inline, blank_e))

            parsed = parse_html(test_str, test_pr, urlize_all=False)
            self.assertEqual(parsed, frame % (expected_inline, blank, expected_inline, blank))

            frame = '<p>test %s</p>\n<a href="foo">%s</a>\n<a href="foo2">%s</a>\n<p>and finally %s</p>'

            test_str = frame % (url, blank, url, blank)

            parsed = parse_html(test_str, test_pr)
            self.assertEqual(parsed, frame % (expected_inline, blank, url, blank_e))

            parsed = parse_html(test_str, test_pr, urlize_all=False)
            self.assertEqual(parsed, frame % (expected_inline, blank, url, blank))

    def test_extract(self):
        blank = 'http://fapp.io/foo/'
        frame = 'test %s\n%s\n%s\n%s at last'
        frame_html = '<p>test %s</p><p><a href="foo">%s</a> %s</p><p>%s</p>'

        for url, expected in self.data_pairs.items():
            all_urls, extracted = extract(frame % (url, blank, url, blank), pr)
            self.assertEqual(all_urls, set([blank, url]))

            if 'url' not in expected:
                expected['url'] = url
            self.assertEqual(extracted, {url: expected})

            all_urls, extracted = extract_html(frame_html % (url, url, blank, blank), pr)
            self.assertEqual(all_urls, set([blank, url]))

            if 'url' not in expected:
                expected['url'] = url
            self.assertEqual(extracted, {url: expected})
    
    def test_outside_of_markup(self):
        frame = '%s<p>testing</p>'
        for url, expected in self.full_pairs.items():
            parsed = parse_html(frame % (url), test_pr)
            self.assertEqual(parsed, frame % (expected))