import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.intrepid.watchdog',
  appName: 'WatchDog',
  webDir: 'out',
  server: {
    url: 'https://neighbourhood-watch-dog.vercel.app/auth/login',
    cleartext: false
  }
};

export default config;
