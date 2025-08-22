def define_env(env):
    @env.macro
    def spec_header(version=None, status=None, owner=None, date=None):
        m = env.page.meta.get('spec', {}) if hasattr(env, 'page') and env.page and env.page.meta else {}
        version = version or m.get('version', '')
        status  = status  or m.get('status', '')
        owner   = owner   or m.get('owner',  '')
        date    = date    or m.get('date',   '')

        # Если ничего не задано — не выводим блок вовсе
        if not any([version, status, owner, date]):
            return ''

        return f'''
!!! info "Спецификация"
    **Версия:** {version} | **Статус:** {status} | **Владелец:** {owner} | **Дата:** {date}
'''.strip()
