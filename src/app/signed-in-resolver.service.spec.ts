import { TestBed } from '@angular/core/testing';

import { SignedInResolverService } from './signed-in-resolver.service';

describe('SignedInResolverService', () => {
  let service: SignedInResolverService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SignedInResolverService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
