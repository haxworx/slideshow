#!/usr/bin/perl

use strict;
use warnings;

use CGI qw/:standard/;
use Template;
use Mail;
use DBI;
use CGI::Cookie;

require './config.pl';

our $DISK_USAGE;

my $cgi = CGI->new();
my $action = $cgi->param("action");
if ($action eq "logout") {
	my $cookie = cookie( -name => "auth",
		             -value => 0);
	print "Set-Cookie: $cookie\n";
        print $cgi->redirect("/");
        exit 0;
}

my $cookie = $cgi->cookie("auth");
my $username = $cgi->cookie("username");
my $password = "";
my $status = check_cookie($cookie, $username);
my $directory = $cgi->param("directory");

if ($status) {
        $username = $cgi->cookie("username");
        my $dbh = dbh_connect();
        my $SQL = "SELECT password FROM users WHERE username = ?";
        my $sth = $dbh->prepare($SQL);
        $sth->execute($username);
        $password = $sth->fetchrow();
} else {
        $username = $cgi->param("username");
        $password = $cgi->param("password");
        if ($password eq "") {
                $password = $cgi->cookie("password");
        }
if ($username eq "") {
        browser_message("You did not input a valid username." , "");
}
if ($password eq "") {
        $password = $cgi->param("password");
}
if ($password eq "") {
        browser_message("You did not input a valid password.", "");
}
}

if ($password eq "") {
	$password = $cgi->param("password");
}

my $message = ""; ### FIXME FIX FIXME and template/control-panel

my $path = "$directory";
if ($directory eq $username) {
	$path = $username;
} elsif ($directory eq "") {
	$path = $username;
	$directory = $path; 
 
} else {
	$path = "$username/$directory";
} 


my @pictures = ();
my $i = 0;
my $dbh = dbh_connect();
my $SQL = "SELECT * FROM files WHERE directory = ? ORDER BY -number";
my $sth = $dbh->prepare($SQL);
$sth->execute($path);
while(defined(my $file = $sth->fetchrow_hashref())) {
        if ($file->{'name'} =~ /.+[\.jpg|\.JPG|\.png|\.PNG]\z/) {
           	$pictures[$i++] = $file;
      	}
}		

$SQL = "SELECT userid FROM users WHERE username = ?";
$sth = $dbh->prepare($SQL);
$sth->execute($username);
my $id = $sth->fetchrow();

$SQL = "SELECT email FROM projects WHERE id = ?";
$sth = $dbh->prepare($SQL);
$sth->execute($id);
my $email = $sth->fetchrow();
$SQL = "SELECT name FROM projects WHERE id = ?";
$sth = $dbh->prepare($SQL);
$sth->execute($id);
my $author = $sth->fetchrow();

use Template;
my $pictures_template = "templates/pictures";

my $vars = {
        USERNAME => $username,
        EMAIL => $email,
        PICTURES => \@pictures,
	AUTHOR => $author,
};
	
my $template = Template->new();

my $html = "";

$template->process($pictures_template, $vars, \$html) or print "$html $!\n\n";
my $portfolio = ""; # what'll it be?
$portfolio = "users" . "/" . $username . "/" . $directory if ($directory ne "");
$portfolio = "users" . "/" . $username if ($directory eq $username);
my $file = "$portfolio/index.html";
open(FH, ">$file");
print FH $html;
close FH;


if ($action eq "rmdir") {
	if ($directory ne "" && $username ne "") {
		if ($path eq $username) { } else {
		`rm -rf \"users/$path\"`;		
		my $dbh = dbh_connect();
		my $SQL = "SELECT userid FROM users WHERE username = ?";
		my $sth = $dbh->prepare($SQL);
		$sth->execute($username);

		my $id = $sth->fetchrow();

		$SQL = "DELETE FROM files WHERE id = ? AND directory = ?";
		$sth = $dbh->prepare($SQL);
		$sth->execute($id, $directory);
		$directory = "";
		my $cgi = CGI->new();
		print $cgi->redirect( -location => "/myPortfolio/portal.cgi" );
		exit;	
		}
	}
}
my $c = CGI->new();
my $submit = $cgi->param("submit");
my @items = $c->param('checkbox');
if ($submit eq "Delete") { 
foreach (@items) {
	my $filename = $_;
	my $username = $cgi->param("username");
	my $directory = $cgi->param("directory");
	my $full_path = "$filename";
	unlink($full_path);
	my $thumbnail = "$full_path-small.jpg";
	unlink($thumbnail);

	my $dbh = dbh_connect();
	my $SQL = "SELECT userid FROM users WHERE username = ?";
	my $sth = $dbh->prepare($SQL);
	$sth->execute($username);

	my $id = $sth->fetchrow();

	$SQL = "DELETE FROM files WHERE id = ? AND name = ?";
	$sth = $dbh->prepare($SQL);
	$message = "deletion processed";
	$sth->execute($id, $filename);
	
	}
	     my $cgi = CGI->new();
        print $cgi->redirect( -location => "/myPortfolio/portal.cgi" );
        exit;
}

if ($action eq "description") {
	foreach (@items) {
        my $filename = $_;
        my $username = $cgi->param("username");
        my $description = $cgi->param("description");
        my $order = $cgi->param("number");
        my $dbh = dbh_connect();
        my $SQL = "SELECT userid FROM users WHERE username = ?";
        my $sth = $dbh->prepare($SQL);
        $sth->execute($username);
        my $id = $sth->fetchrow();

        $SQL = "UPDATE files SET description = ?, number = ? WHERE id = ? AND name = ?";
        $sth = $dbh->prepare($SQL);
        $sth->execute($description, $order, $id, $filename);
        $message = "Updated details for $filename.";
	}
	my $cgi = CGI->new();
	print $cgi->redirect( -location => "/myPortfolio/portal.cgi" );
	exit;
}
my $ROOT_DIR = "users";

if ($action eq "mkdir") {
	$path = "$ROOT_DIR/$path";
	if ($path =~ /\.\./) {
		browser_message("St0p try1ng to hax0r m3!");
		exit 0;
	}
	if ($directory eq "") {
		browser_message("That won't work!");
		exit 0;
	}
	mkdir($path);
	$message = "Directory $path is created.";
	$path = "$username/$directory";
        my $cgi = CGI->new();
        print $cgi->redirect( -location => "/myPortfolio/portal.cgi");
	exit;
}

if ($action eq "password") {
	my $dbh = dbh_connect();
        my $password = $cgi->param("password");
        my $secondary = $cgi->param("secondary");
        my $username = $cgi->param("username");
        if ($password eq "" || $secondary eq "") {
                browser_message("You can not use an empty password.", $username);
        }
        if ($password ne $secondary) {
                browser_message("You must enter your password correctly twice in order to change it, try again.", $username);
        }

        if ($password eq "" || $secondary eq "") {
                browser_messge("Empty fields, try again.");
        }

        my $SQL = "UPDATE users SET password = ? WHERE username = ?";
        my $sth = $dbh->prepare($SQL);
        $sth->execute($cgi->param("password"), $cgi->param("username"));

	$dbh->disconnect();
	$message = "Password successfully changed.";
	my $cgi = CGI->new();
	print $cgi->redirect( -location => "/myPortfolio/portal.cgi");
	exit;
}

$dbh = dbh_connect();
$SQL = "SELECT userid FROM users WHERE username = ? AND password = ? AND active = '1'";
$sth = $dbh->prepare($SQL) || browser_message("oh no!", $username);
$sth->execute($username, $password);
my $userid = $sth->fetchrow();
if ($userid eq "") {
	browser_message("Invalid username or password, please try again.", ""); 
}
$SQL = "SELECT active FROM projects WHERE id = ?";
$sth = $dbh->prepare($SQL);
$sth->execute($userid);
$status = $sth->fetchrow();
if ($status ne "") {
	my $template_path = "templates/portal";
	$SQL = "SELECT * FROM projects WHERE id = ?";
	$sth = $dbh->prepare($SQL);
	$sth->execute($userid);
	my $tmp = $sth->fetchrow_hashref();
	my $author = "";
	$author = $tmp->{'name'}; #XXX COPYRIGHT!
	my $storage = calculate_disk_usage("users/$username");
	$SQL = "SELECT * from files WHERE id = ? AND directory = ? ORDER by -number";
	$sth = $dbh->prepare($SQL);
	$sth->execute($userid, $path); # FIXME$directory);
	my @files = ();
	my $i = 0;	

	$storage .= "MB";
	while(defined(my $file = $sth->fetchrow_hashref())) {
		$files[$i++] = $file;
	}

	#XXX SQL SORTS @files = sort ({ $a->{name} cmp $b->{name} } @files);
	@files = files_table(@files);
	my @dirs = read_dirs($username);
	
	my $CWD = "$path";

	my $vars = {
		DETAILS => $tmp,
		USERNAME => $username,
		FILES => \@files,
		STORAGE => $storage,
		QUOTA => "250MB",
		DIRS => \@dirs,
		CWD => $CWD,
		MESSAGE => $message,
		AUTHOR => $author,
	};

	use Template;

	my $template = Template->new();

	create_cookie($username, $password, $directory);

	$template->process($template_path, $vars);

	exit 0;
}

print $cgi->redirect( location => "/myPortfolio/portal.cgi");

exit 0;
