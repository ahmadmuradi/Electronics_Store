import { NavigatorScreenParams } from '@react-navigation/native';

export type RootStackParamList = {
  ProductList: undefined;
  ProductDetail: { productId: string };
  StockUpdate: { productId: string };
};

export type RootTabParamList = {
  Home: undefined;
  Products: NavigatorScreenParams<RootStackParamList>;
  Settings: undefined;
};

// This helps with type checking the route names
export type ScreenName = keyof RootStackParamList;

// Extend the default navigation types
declare global {
  namespace ReactNavigation {
    type RootParamList = RootStackParamList;
  }
}
