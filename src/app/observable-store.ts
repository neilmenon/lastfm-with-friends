import { AnyAction, Store } from 'redux';
import { BehaviorSubject, interval, Observable, of } from 'rxjs';
import { distinctUntilChanged, map } from 'rxjs/operators';

import { Injectable } from '@angular/core';
import { NgZone } from '@angular/core';
import { getInstanceSelection } from './helpers';
import { Selector, Transformer } from './selectors';
import { AppState } from './store';

export type Comparator = (x: any, y: any) => boolean;

/**
 * This interface represents the glue that connects the
 * subscription-oriented Redux Store with the RXJS Observable-oriented
 * Angular component world.
 *
 * Augments the basic Redux store interface with methods to
 * enable selection
 */
@Injectable({ providedIn: 'root' })
export class ObservableStore<StateType> {
  static instance?: ObservableStore<any> = undefined;
  private reduxStore: Store<StateType> | undefined = undefined;
  private state$: BehaviorSubject<StateType>;

  constructor(private ngZone: NgZone) {
    ObservableStore.instance = this;
    this.state$ = new BehaviorSubject(null);
  }

  provideStore(store: Store<StateType>) {
    this.reduxStore = store;
    this.reduxStore.subscribe(() => this.state$.next(this.reduxStore.getState()));
  };

  /**
   * This method can be used to get some part of the redux state synchronously
   */
  getState<SelectedType>(selector?: (state: StateType) => SelectedType): SelectedType {
    return selector(this.reduxStore.getState());
  }

  /**
   * This method can be used to get some part of the redux state asynchronously
   */
  select<SelectedType>(selector?: (state: StateType) => SelectedType, comparator?: Comparator): Observable<SelectedType> {
    return this.state$.asObservable().pipe(
      distinctUntilChanged(),
      map(state => selector(state)),
      distinctUntilChanged(comparator)
    );
  }

  dispatch<A extends AnyAction>(action: A) {
    return NgZone.isInAngularZone() ?
      this.reduxStore.dispatch(action) :
      this.ngZone.run(() => this.reduxStore.dispatch(action));
  };

  subscribe(listener: () => void) {
    return this.reduxStore.subscribe(listener);
  }

}

/**
 * Selects an observable from the store, and attaches it to the decorated
 * property.
 *
 * ```ts
 *  import { select } from '@angular-redux/store';
 *
 *  class SomeClass {
 *    @select(['foo','bar']) foo$: Observable<string>
 * }
 * ```
 *
 * @param selector
 * A selector function, property name string, or property name path
 * (array of strings/array indices) that locates the store data to be
 * selected
 *
 * @param comparator Function used to determine if this selector has changed.
 */
export function select<T>(
  selector?: Selector<AppState, T>,
  comparator?: Comparator
): PropertyDecorator {
  return (target: any, key: string | symbol): void => {
    const adjustedSelector = selector
      ? selector
      : String(key).lastIndexOf('$') === String(key).length - 1
        ? String(key).substring(0, String(key).length - 1)
        : key;
    decorate(adjustedSelector, undefined, comparator)(target, key);
  };
}

/**
 * Selects an observable using the given path selector, and runs it through the
 * given transformer function. A transformer function takes the store
 * observable as an input and returns a derived observable from it. That derived
 *  observable is run through distinctUntilChanges with the given optional
 * comparator and attached to the store property.
 *
 * Think of a Transformer as a FunctionSelector that operates on observables
 * instead of values.
 *
 * ```ts
 * import { select$ } from 'angular-redux/store';
 *
 * export const debounceAndTriple = obs$ => obs$
 *  .debounce(300)
 *  .map(x => 3 * x);
 *
 * class Foo {
 *  @select$(['foo', 'bar'], debounceAndTriple)
 *  readonly debouncedFooBar$: Observable<number>;
 * }
 * ```
 */
export function select$<T>(
  selector: Selector<any, T>,
  transformer: Transformer<any, T>,
  comparator?: Comparator
): PropertyDecorator {
  return decorate(selector, transformer, comparator);
}

function decorate(
  selector: Selector<any, any>,
  transformer?: Transformer<any, any>,
  comparator?: Comparator
): PropertyDecorator {
  return function decorator(target: any, key): void {
    function getter(this: any) {
      return getInstanceSelection(this, key, selector, transformer, comparator);
    }

    // Replace decorated property with a getter that returns the observable.
    if (delete target[key]) {
      Object.defineProperty(target, key, {
        get: getter,
        enumerable: true,
        configurable: true,
      });
    }
  };
}