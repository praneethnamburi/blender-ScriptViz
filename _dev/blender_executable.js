"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
const os = require("os");
const path = require("path");
const vscode = require("vscode");
const child_process = require("child_process");
const paths_1 = require("./paths");
const communication_1 = require("./communication");
const select_utils_1 = require("./select_utils");
const utils_1 = require("./utils");
const addon_folder_1 = require("./addon_folder");
class BlenderExecutable {
    constructor(data) {
        this.data = data;
    }
    static GetAny() {
        return __awaiter(this, void 0, void 0, function* () {
            let data = yield getFilteredBlenderPath({
                label: 'Blender Executable',
                selectNewLabel: 'Choose a new Blender executable...',
                predicate: () => true,
                setSettings: () => { }
            });
            return new BlenderExecutable(data);
        });
    }
    static GetDebug() {
        return __awaiter(this, void 0, void 0, function* () {
            let data = yield getFilteredBlenderPath({
                label: 'Debug Build',
                selectNewLabel: 'Choose a new debug build...',
                predicate: item => item.isDebug,
                setSettings: item => { item.isDebug = true; }
            });
            return new BlenderExecutable(data);
        });
    }
    static LaunchAny() {
        return __awaiter(this, void 0, void 0, function* () {
            yield (yield this.GetAny()).launch();
        });
    }
    static LaunchDebug(folder) {
        return __awaiter(this, void 0, void 0, function* () {
            yield (yield this.GetDebug()).launchDebug(folder);
        });
    }
    get path() {
        return this.data.path;
    }
    launch() {
        return __awaiter(this, void 0, void 0, function* () {
            let execution = new vscode.ProcessExecution(this.path, getBlenderLaunchArgs(), { env: yield getBlenderLaunchEnv() });
            yield utils_1.runTask('blender', execution);
        });
    }
    launchDebug(folder) {
        return __awaiter(this, void 0, void 0, function* () {
            let configuration = {
                name: 'Debug Blender',
                type: 'cppdbg',
                request: 'launch',
                program: this.data.path,
                args: ['--debug'].concat(getBlenderLaunchArgs()),
                env: yield getBlenderLaunchEnv(),
                stopAtEntry: false,
                MIMode: 'gdb',
                cwd: folder.uri.fsPath,
            };
            vscode.debug.startDebugging(folder.folder, configuration);
        });
    }
    launchWithCustomArgs(taskName, args) {
        return __awaiter(this, void 0, void 0, function* () {
            let execution = new vscode.ProcessExecution(this.path, args);
            yield utils_1.runTask(taskName, execution, true);
        });
    }
}
exports.BlenderExecutable = BlenderExecutable;
function getFilteredBlenderPath(type) {
    return __awaiter(this, void 0, void 0, function* () {
        let config = utils_1.getConfig();
        let allBlenderPaths = config.get('executables');
        let usableBlenderPaths = allBlenderPaths.filter(type.predicate);
        let items = [];
        for (let pathData of usableBlenderPaths) {
            let useCustomName = pathData.name !== '';
            items.push({
                data: () => __awaiter(this, void 0, void 0, function* () { return pathData; }),
                label: useCustomName ? pathData.name : pathData.path
            });
        }
        items.push({ label: type.selectNewLabel, data: () => __awaiter(this, void 0, void 0, function* () { return askUser_FilteredBlenderPath(type); }) });
        let item = yield select_utils_1.letUserPickItem(items);
        let pathData = yield item.data();
        if (allBlenderPaths.find(data => data.path === pathData.path) === undefined) {
            allBlenderPaths.push(pathData);
            config.update('executables', allBlenderPaths, vscode.ConfigurationTarget.Global);
        }
        return pathData;
    });
}
function askUser_FilteredBlenderPath(type) {
    return __awaiter(this, void 0, void 0, function* () {
        let filepath = yield askUser_BlenderPath(type.label);
        let pathData = {
            path: filepath,
            name: '',
            isDebug: false,
        };
        type.setSettings(pathData);
        return pathData;
    });
}
function askUser_BlenderPath(openLabel) {
    return __awaiter(this, void 0, void 0, function* () {
        let value = yield vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: false,
            openLabel: openLabel
        });
        if (value === undefined)
            return Promise.reject(utils_1.cancel());
        let filepath = value[0].fsPath;
        if (os.platform() === 'darwin') {
            if (filepath.toLowerCase().endsWith('.app')) {
                filepath += '/Contents/MacOS/blender';
            }
        }
        yield testIfPathIsBlender(filepath);
        return filepath;
    });
}
function testIfPathIsBlender(filepath) {
    return __awaiter(this, void 0, void 0, function* () {
        let name = path.basename(filepath);
        if (!name.toLowerCase().startsWith('blender')) {
            return Promise.reject(new Error('Expected executable name to begin with \'blender\''));
        }
        let testString = '###TEST_BLENDER###';
        let command = `"${filepath}" --factory-startup -b --python-expr "import sys;print('${testString}');sys.stdout.flush();sys.exit()"`;
        return new Promise((resolve, reject) => {
            child_process.exec(command, {}, (err, stdout, stderr) => {
                let text = stdout.toString();
                console.log(text)
                if (false) {
                    var message = 'A simple check to test if the selected file is Blender failed.';
                    message += ' Please create a bug report when you are sure that the selected file is Blender 2.8 or newer.';
                    message += ' The report should contain the full path to the executable.';
                    reject(new Error(message));
                }
                else {
                    resolve();
                }
            });
        });
    });
}
function getBlenderLaunchArgs() {
    return ['--env-system-python', 'C:\\Users\\Praneeth\\.conda\\envs\\blender2830', '--python', paths_1.launchPath];
}
function getBlenderLaunchEnv() {
    return __awaiter(this, void 0, void 0, function* () {
        let config = utils_1.getConfig();
        let addons = yield addon_folder_1.AddonWorkspaceFolder.All();
        let loadDirsWithNames = yield Promise.all(addons.map(a => a.getLoadDirectoryAndModuleName()));
        return {
            ADDONS_TO_LOAD: JSON.stringify(loadDirsWithNames),
            EDITOR_PORT: communication_1.getServerPort().toString(),
            ALLOW_MODIFY_EXTERNAL_PYTHON: config.get('allowModifyExternalPython') ? 'yes' : 'no',
        };
    });
}
//# sourceMappingURL=blender_executable.js.map