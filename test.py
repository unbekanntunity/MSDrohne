import gettext

language = 'de_DE'
translation = gettext.translation('base', localedir='locales', languages=[language])
translation.install()

str = translation.gettext('Connect to device').encode("latin-1").decode("utf-8")
print(str)