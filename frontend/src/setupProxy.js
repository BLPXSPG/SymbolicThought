
const { createProxyMiddleware } = require('http-proxy-middleware')    //现在的
// const proxy = require("http-proxy-middleware");        //原来的

module.exports = function (app) {
  app.use(
    createProxyMiddleware('/apilocal', {      //这里也要改成createProxyMiddleware
      target: process.env.API_TARGET || 'http://localhost:5003',
      changeOrigin: true,
      pathRewrite: { '^/apilocal': '' },
    })
  )
}
