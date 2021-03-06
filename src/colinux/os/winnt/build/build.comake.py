def optional_targets():
    import os
    from os import getenv
    enable_wx = getenv('COLINUX_ENABLE_WX')
    if enable_wx:
        if enable_wx == "yes":
            return [Input('colinux-console-wx.exe')]
    return []

targets['executables'] = Target(
    inputs=[
    Input('colinux-daemon.exe'),
    Input('colinux-net-daemon.exe'),
    Input('colinux-console-fltk.exe'),
    Input('colinux-debug-daemon.exe'),
    Input('colinux-console-nt.exe'),
    Input('colinux-bridged-net-daemon.exe'),
    Input('colinux-ndis-net-daemon.exe'),
    Input('colinux-slirp-net-daemon.exe'),
    Input('colinux-serial-daemon.exe'),
    Input('linux.sys'),
    ] + optional_targets(),
    tool = Empty(),
)

def generate_options(compiler_def_type, libs=None, lflags=None):
    if not libs:
        libs = []
    if not lflags:
        lflags = []
    return Options(
        overriders = dict(
            compiler_def_type = compiler_def_type,
            compiler_strip = False,
        ),
        appenders = dict(
        compiler_flags = [ '-mno-cygwin' ],
        linker_flags = lflags,
        compiler_libs = libs + [
            'user32', 'gdi32', 'ws2_32', 'ntdll', 'kernel32', 'ole32', 'uuid', 'gdi32',
            'msvcrt', 'crtdll', 'shlwapi',
        ]),
    )

def generate_wx_options():
    return Options(
        overriders = dict(
            compiler_def_type = 'g++',
            compiler_strip = True,
        ),
        appenders = dict(
                compiler_flags = [ '`wx-config --cxxflags`' ],
                linker_add = [ '`wx-config --libs`' ],
        )
    )

user_dep = [Input('../user/user-all.a')]
user_res = [Input('../user/daemon/res/colinux.res')]
daemon_res = [Input('../user/daemon/res/daemon.res')]

targets['colinux-daemon.exe'] = Target(
    inputs = daemon_res + [
        Input('../user/daemon/daemon.o'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('gcc'),
)

targets['colinux-net-daemon.exe'] = Target(
    inputs = user_res + [
       Input('../user/conet-daemon/build.a'),
       Input('../../../user/daemon-base/build.a'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('g++'),
)

targets['colinux-bridged-net-daemon.exe'] = Target(
    inputs = user_res + [
       Input('../user/conet-bridged-daemon/build.o'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('gcc', libs=['wpcap']),
)

targets['colinux-ndis-net-daemon.exe'] = Target(
    inputs = user_res + [
       Input('../user/conet-ndis-daemon/build.o'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('gcc'),
)

targets['colinux-slirp-net-daemon.exe'] = Target(
    inputs = user_res + [
       Input('../user/conet-slirp-daemon/build.o'),
       Input('../../../user/slirp/build.o'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('gcc', libs=['iphlpapi']),
)

targets['colinux-serial-daemon.exe'] = Target(
    inputs = user_res + [
       Input('../user/coserial-daemon/build.o'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('gcc'),
)

targets['colinux-console-fltk.exe'] = Target(
    inputs = user_res + [
       Input('../user/console-fltk/build.a'),
       Input('../../../user/console-fltk/build.a'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('g++', libs=['fltk', 'mingw32'], lflags=['-mwindows']),
)

targets['colinux-console-nt.exe'] = Target(
    inputs = user_res + [
       Input('../user/console-nt/build.a'),
       Input('../../../user/console-nt/build.a'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('g++'),
)

targets['colinux-console-wx.exe'] = Target(
    inputs = user_res + [
        Input('../../../user/console-wx/build.o'),
    ],
    tool = Compiler(),
    mono_options = generate_wx_options(),
)

targets['colinux-debug-daemon.exe'] = Target(
    inputs = user_res + [
       Input('../user/debug/build.o'),
       Input('../../../user/debug/build.o'),
    ] + user_dep,
    tool = Compiler(),
    mono_options = generate_options('gcc'),
)

targets['driver.o'] = Target(
    inputs = [
       Input('../../../kernel/build.o'),
       Input('../kernel/build.o'),
       Input('../../../arch/build.o'),
       Input('../../../common/common.a'),
    ],
    tool = Linker(),
)

def script_cmdline(scripter, tool_run_inf):
    from comake.settings import settings
    if settings.arch == 'x86_64':
        driver_entry = 'DriverEntry'
    else:
        driver_entry = '_DriverEntry@8'
    inputs = tool_run_inf.target.get_actual_inputs()
    command_line = ((
        "%s "
        "-Wl,--strip-debug "
        "-Wl,--subsystem,native "
        "-Wl,--image-base,0x10000 "
        "-Wl,--entry,%s "
        "-shared -nostartfiles -nostdlib "
        "-o %s %s -lndis -lntoskrnl -lhal ") %
    (scripter.get_cross_build_tool('gcc', tool_run_inf),
     driver_entry,
     tool_run_inf.target.pathname,
     inputs[0].pathname))
    return command_line

def get_ddk_include():
    from comake.settings import settings
    return getenv('PREFIX') + '/' + settings.gcc_host_target + '/include/ddk'

targets['linux.sys'] = Target(
    tool = Script(script_cmdline),
    inputs = [
       Input('driver.o'),
    ],
    options = Options(
        appenders = dict(
            compiler_defines = dict(
                __KERNEL__=None,
                CO_KERNEL=None,
                CO_HOST_KERNEL=None,
            ),
            compiler_includes = [ get_ddk_include() ],
        )
    )
)

targets['installer'] = Target(
    inputs = [
       Input('executables'),
       Input('../user/install/coLinux.exe'),
    ],
    tool = Empty(),
)
