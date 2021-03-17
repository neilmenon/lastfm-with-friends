import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { MatSliderModule } from '@angular/material/slider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule } from '@angular/material/paginator';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HeaderComponent } from './header/header.component';
import { LayoutModule } from '@angular/cdk/layout';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatMomentDateModule } from '@angular/material-moment-adapter';
import { LastfmauthComponent } from './lastfmauth/lastfmauth.component';
import { HomeComponent } from './home/home.component';
import { MessagesComponent } from './messages/messages.component';
import { SignoutComponent } from './signout/signout.component';
import { UserService } from './user.service';
import { CreateGroupComponent } from './create-group/create-group.component';
import { ReactiveFormsModule } from '@angular/forms';
import { GroupDetailComponent } from './group-detail/group-detail.component';
import { JoinGroupComponent } from './join-group/join-group.component';
import { GroupDashboardComponent } from './group-dashboard/group-dashboard.component';
import { EditGroupComponent } from './edit-group/edit-group.component';
import { ScrobbleHistoryComponent } from './scrobble-history/scrobble-history.component';
import { UserSettingsComponent } from './user-settings/user-settings.component';
import { WhoKnowsTopComponent } from './who-knows-top/who-knows-top.component';
import { CustomDateRangeComponent } from './custom-date-range/custom-date-range.component';

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    LastfmauthComponent,
    HomeComponent,
    MessagesComponent,
    SignoutComponent,
    CreateGroupComponent,
    GroupDetailComponent,
    JoinGroupComponent,
    GroupDashboardComponent,
    EditGroupComponent,
    ScrobbleHistoryComponent,
    UserSettingsComponent,
    WhoKnowsTopComponent,
    CustomDateRangeComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatSliderModule,
    LayoutModule,
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatIconModule,
    MatListModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatMenuModule,
    MatDialogModule,
    MatTooltipModule,
    MatFormFieldModule,
    HttpClientModule,
    MatInputModule,
    ReactiveFormsModule,
    MatExpansionModule,
    MatProgressBarModule,
    MatSelectModule,
    MatPaginatorModule,
    FormsModule,
    MatDatepickerModule,
    MatMomentDateModule,
    RouterModule.forRoot([
      {path: '', component: HomeComponent},
      {path: 'lastfmauth', component: LastfmauthComponent},
      {path: 'signout', component: SignoutComponent},
      {path: 'groups/create', component: CreateGroupComponent},
      {path: 'groups/join', component: JoinGroupComponent},
      {path: 'groups/:joinCode', component: GroupDetailComponent},
      {path: 'groups/:joinCode/edit', component: EditGroupComponent},
      {path: 'settings', component: UserSettingsComponent}
    ])
  ],
  providers: [UserService],
  bootstrap: [AppComponent]
})
export class AppModule { }
