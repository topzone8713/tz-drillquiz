const { defineConfig } = require('@vue/cli-service')

// 환경 설정
const ENVIRONMENT = process.env.ENVIRONMENT || 'development'

// 환경변수에서 서버 설정 가져오기
const DJANGO_HOST = process.env.DJANGO_HOST || 'localhost'
const DJANGO_PORT = process.env.DJANGO_PORT || '8000'

const FRONTEND_PORT = process.env.FRONTEND_PORT || '8080'

// vue-cli-service serve가 실행 중인지 확인 (개발 서버)
const isDevServer = process.argv.includes('serve') || process.argv.includes('serve.js')

// 개발 서버 실행 중이면 항상 로컬 백엔드 사용 (환경 변수 무시)
// 환경에 따른 설정
const isProduction = ENVIRONMENT === 'production' && !isDevServer

// 개발 환경에서는 항상 localhost:8000 사용
const targetHost = isDevServer ? '127.0.0.1' : (isProduction ? DJANGO_HOST : '127.0.0.1')
const targetPort = isDevServer ? '8000' : (isProduction ? DJANGO_PORT : '8000')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    host: 'localhost', // localhost로 제한
    port: parseInt(FRONTEND_PORT),
    historyApiFallback: true,
    allowedHosts: 'all', // 모든 호스트 허용
    client: {
      webSocketURL: 'ws://localhost:' + parseInt(FRONTEND_PORT) + '/ws',
      overlay: {
        warnings: false,
        errors: true
      }
    },
    webSocketServer: {
      type: 'ws',
      options: {
        host: 'localhost',
        port: parseInt(FRONTEND_PORT)
      }
    },
    proxy: {
      '/api': {
        target: `http://${targetHost}:${targetPort}`,
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        onProxyReq: (proxyReq, req) => {
          console.log(`[Proxy] ${req.method} ${req.url} -> ${targetHost}:${targetPort}${req.url}`)
        },
        onProxyRes: (proxyRes, req) => {
          console.log(`[Proxy] Response: ${req.method} ${req.url} -> ${proxyRes.statusCode}`)
        },
        onError: (err, req) => {
          console.error(`[Proxy] Error: ${req.method} ${req.url}`, err)
        }
      }
    }
  },
  outputDir: 'dist',
  publicPath: '/',
  productionSourceMap: !isProduction, // 프로덕션에서는 소스맵 비활성화
  configureWebpack: {
    devtool: isProduction ? false : 'source-map', // 프로덕션에서는 소스맵 비활성화
    // ios 브랜치에서는 Capacitor 패키지가 설치되어 있으므로 externals 제거
    // Capacitor는 optional import로 처리하여 웹 환경에서도 동작하도록 함
    resolve: {
      fallback: {
        http: false,
        https: false,
        crypto: false,
        util: false,
        stream: false,
        zlib: false,
        events: false,
        url: false,
        assert: false,
        'follow-redirects': false,
        net: false,
        tls: false,
        fs: false,
        path: false,
        os: false
      }
    },
    plugins: [
      // follow-redirects를 빈 모듈로 대체 (브라우저 환경에서는 필요 없음)
      new (require('webpack').NormalModuleReplacementPlugin)(
        /^follow-redirects$/,
        require.resolve('./src/utils/empty-module.js')
      )
    ],
    optimization: {
      minimizer: process.env.NODE_ENV === 'production' ? [
        (compiler) => {
          const TerserPlugin = require('terser-webpack-plugin')
          new TerserPlugin({
            terserOptions: {
              compress: {
                // console.log는 제거하되, debugLog는 유지하기 위해 조건부 제거
                // drop_console을 false로 설정하여 디버깅 가능하도록 유지
                drop_console: false, // 디버깅을 위해 console.log 유지
                drop_debugger: true,
                // pure_funcs를 사용하여 특정 함수만 제거할 수도 있음
                // pure_funcs: ['console.log', 'console.info'] // 필요시 사용
              }
            }
          }).apply(compiler)
        }
      ] : []
    }
  }
}) 