import { AnyAction, Store } from 'redux';
import { BehaviorSubject, Observable } from 'rxjs';
import { distinctUntilChanged, map } from 'rxjs/operators';

import { Injectable } from '@angular/core';
import { NgZone } from '@angular/core';

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

  private reduxStore: Store<StateType> | undefined = undefined;
  private state$: BehaviorSubject<StateType>;

  constructor(private ngZone: NgZone) {
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
