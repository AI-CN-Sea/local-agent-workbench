export default {
  preview: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  },
  build: {
    emptyOutDir: false
  }
};
