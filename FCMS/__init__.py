from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    with Configurator(settings=settings) as config:
        my_session_factory = SignedCookieSessionFactory(settings['session_secret'])
        config.include('.security')
        config.include('.models')
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('pyramid_storage')
        config.add_static_view('storage', 'storage')
        config.set_session_factory(my_session_factory)
        config.scan()
    return config.make_wsgi_app()
