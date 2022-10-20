import { Observable } from 'rxjs';

/**
 * Custom equality checker that can be used with `.select` and `@select`.
 * ```ts
 * const customCompare: Comparator = (x: any, y: any) => {
 *  return x.id === y.id
 * }
 *
 * @select(selector, customCompare)
 * ```
 */
export type Comparator = (x: any, y: any) => boolean;
export type Transformer<RootState, V> = (
  store$: Observable<RootState>,
  scope: any
) => Observable<V>;
export type PropertySelector = string | number | symbol;
export type PathSelector = (string | number)[];
export type FunctionSelector<RootState, S> = ((s: RootState) => S);
export type Selector<RootState, S> =
  | PropertySelector
  | PathSelector
  | FunctionSelector<RootState, S>;


