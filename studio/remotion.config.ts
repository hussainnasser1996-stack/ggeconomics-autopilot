import { Config } from "@remotion/cli/config";
// Mac: use the installed Chrome. Cloud (Linux): Remotion downloads its own headless shell.
if (process.platform === "darwin") {
  Config.setBrowserExecutable("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
  Config.setChromeMode("chrome-for-testing");
}
