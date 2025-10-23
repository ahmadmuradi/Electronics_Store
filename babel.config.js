module.exports = function (api) {
  api.cache(true);

  const presets = [
    'babel-preset-expo',
    [
      '@babel/preset-env',
      {
        targets: {
          node: 'current',
        },
      },
    ],
    '@babel/preset-react',
    '@babel/preset-typescript',
  ];

  const plugins = [
    [
      'module-resolver',
      {
        root: ['./src'],
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
        alias: {
          '@': './src',
        },
      },
    ],
    'react-native-reanimated/plugin',
    '@babel/plugin-proposal-export-namespace-from',
    ['@babel/plugin-transform-class-properties', { loose: true }],
    ['@babel/plugin-transform-private-methods', { loose: true }],
    ['@babel/plugin-transform-private-property-in-object', { loose: true }],
    'react-native-paper/babel',
  ];

  // Only add this plugin in test environment
  if (process.env.NODE_ENV === 'test') {
    plugins.push('@babel/plugin-transform-modules-commonjs');
  }

  return {
    presets,
    plugins,
  };
};
