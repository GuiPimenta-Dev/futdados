import { Config } from "@remotion/cli/config";

// png (não jpeg) => saída yuv420p limited-range, compatível com todo player.
Config.setVideoImageFormat("png");
Config.setPixelFormat("yuv420p");
Config.setConcurrency(4);
Config.overrideWebpackConfig((c) => c);
